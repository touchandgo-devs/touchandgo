import logging
from os import _exit
from time import time

from blessings import Terminal
from touchandgo.decorators import with_config_dir
from touchandgo.download import DownloadManager
from touchandgo.helpers import get_settings
from touchandgo.history import History
from touchandgo.search.leetx import Search1337x
from touchandgo.search.skytorrents import SearchSky


log = logging.getLogger('touchandgo.main')
term = Terminal()


class SearchAndStream(object):
    """Searchs a torrent and start streaming it"""
    @with_config_dir
    def __init__(self, name, season=None, episode=None, sub_lang=None,
                 serve=False, quality=None, port=None, player=None,
                 use_cache=True):
        self.name = name
        self.season = season
        self.episode = episode
        self.sub_lang = sub_lang
        self.serve = serve
        self.quality = quality
        self.port = port
        self.player = player
        self.use_cache = use_cache

    @with_config_dir
    def download(self, results):
        print(term.bold('Downloading Magnet'))
        log.info("Processing magnet link")
        magnet = results['magnet']
        log.info("Magnet: %s", magnet)

        history = History(date=int(time()), name=self.name, season=self.season,
                          episode=self.episode, magnet=magnet)
        history.save()
        history.update()

        manager = DownloadManager(magnet, port=self.port, serve=self.serve,
                                  sub_lang=self.sub_lang, player=self.player)
        manager.start()

    def watch(self):
        print(term.bold('Welcome to Touchandgo'))
        try:
            if self.name.startswith('magnet'):
                results = {'magnet': self.name}
                self.download(results)
            else:
                history = None
                if self.use_cache:
                    history = History.one(name=self.name, season=self.season,
                                          episode=self.episode)
                if history is None or not hasattr(history, "magnet"):
                    self.search_magnet()
                else:
                    results = {'magnet': history.magnet}
                    self.download(results)

        except KeyboardInterrupt:
            log.info("Thanks for using Touchandgo")
            _exit(0)

    def search_magnet(self):
        print ("Searching magnet")
        log.info("Searching magnet")
        self.search_1337x()

    def get_search_string(self):
        search_string = self.name
        if self.season is not None and self.episode is not None:
            search_string += " s%se%s" % (str(self.season).zfill(2),
                                          str(self.episode).zfill(2))
        return search_string

    def search_1337x(self):
        search_string = self.get_search_string()
        print("Searching '%s'" % search_string)
        log.info("Searching %s", search_string)

        settings = get_settings()
        engine = settings.default_search_engine
        if engine == "leet":
            search_class = Search1337x
        else:
            search_class = SearchSky

        search = search_class(search_string)
        results = search.list()
        print(term.clear())
        print(term.bold("Touchandgo\n"))
        print(term.red("Search Results"))
        if not self.serve:
            for i, result in enumerate(results, 1):
                option = term.cyan("%s) " % i)
                option += result['name'] + " "
                option += term.yellow(result['size'])
                option += term.green(" S:" + result['seeds'])
                option += term.red(" L:" + result['leechs'])
                print(option)
            input_text = "Select which torrent you want to download (1-%d): " % \
                len(results)
            user_inuput = raw_input(input_text)
            try:
                opt = int(user_inuput) - 1
                if opt > len(results) or opt < 1:
                    opt = 0
            except ValueError:
                opt = 0
        else:
            opt = 0
        result = search.get_magnet(opt)
        self.download(result)
