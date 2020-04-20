import logging
from os import _exit
from time import time

from blessings import Terminal
from Py1337x import Py1337x
from touchandgo.decorators import with_config_dir
from touchandgo.download import DownloadManager
from touchandgo.history import History


log = logging.getLogger('touchandgo.main')
term = Terminal()


class SearchAndStream:
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
        try:
            if self.name.startswith('magnet'):
                results = {'magnet': self.name}
            else:
                results = {"magnet": self.search_magnet()}
            self.download(results)

        except KeyboardInterrupt:
            log.info("Thanks for using Touchandgo")
            _exit(0)

    def search_magnet(self):
        print("Searching magnet")
        log.info("Searching magnet")
        return self.search_1337x()

    def get_search_string(self):
        search_string = self.name
        if self.season is not None and self.episode is not None:
            search_string += " s%se%s" % (str(self.season).zfill(2),
                                          str(self.episode).zfill(2))
        return search_string

    def search_1337x(self):
        search_string = self.get_search_string()
        print("Searching '%s' on 1337x" % search_string)
        log.info("Searching %s on 1337x", search_string)
        leetClient = Py1337x()
        results = leetClient.search(search_string)
        # print(term.clear())
        # print(term.bold("Touchandgo\n"))
        # print(term.red("1337x Torrents Results"))
        # if not self.serve:
        #     for i, result in enumerate(results, 1):
        #         option = term.cyan("%s) " % i)
        #         option += result['name'] + " "
        #         option += term.yellow(result['size'])
        #         option += term.green(" S:" + result['seeds'])
        #         option += term.red(" L:" + result['leechs'])
        #         print(option)
        #     input_text = "Select which torrent you want to download (1-%d): " % \
        #         len(results)
        #     user_inuput = input(input_text)
        #     try:
        #         opt = int(user_inuput) - 1
        #         if opt > len(results) or opt < 1:
        #             opt = 0
        #     except ValueError:
        #         opt = 0
        # else:
        #     opt = 0
        # result = results[opt].get("MagnetLink")
        # self.download(result)
        return results[0].get("MagnetLink")
