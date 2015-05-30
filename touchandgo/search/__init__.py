from KickassAPI import Search
import logging

from os import _exit
from time import time
from torrentmediasearcher import TorrentMediaSearcher

from touchandgo.decorators import with_config_dir
from touchandgo.download import DownloadManager
from touchandgo.helpers import get_settings
from touchandgo.history import History

from touchandgo.search.strike import StrikeAPI


log = logging.getLogger('touchandgo.main')


class SearchAndStream(object):
    """Searchs a torrent and start streaming it"""
    @with_config_dir
    def __init__(self, name, season=None, episode=None, sub_lang=None,
                 serve=False, quality=None, port=None, player=None,
                 search=None, use_cache=True):
        self.name = name
        self.season = season
        self.episode = episode
        self.sub_lang = sub_lang
        self.serve = serve
        self.quality = quality
        self.port = port
        self.player = player
        if search is None:
            settings = get_settings()
            search = settings.default_search_engine
        self.search_engine = search
        self.use_cache = use_cache

    @with_config_dir
    def download(self, results):
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
        log.info("Searching torrent")
        if self.search_engine == "kat":
            self.kat_search()
        elif self.search_engine == "strike":
            self.strike_search()
        else:
            self.tms_search()

    def get_search_string(self):
        search_string = self.name
        if self.season is not None and self.episode is not None:
            search_string += " s%se%s" % (str(self.season).zfill(2),
                                          str(self.episode).zfill(2))
        return search_string

    def kat_search(self):
        search_string = self.get_search_string()
        log.info("Searching %s on Kickass", search_string)
        results = Search(search_string).list()
        print results
        results = {'magnet': results[0].magnet_link}
        self.download(results)

    def strike_search(self):
        search_string = self.get_search_string()
        log.info("Searching %s on Strike", search_string)
        strike = StrikeAPI(search_string)
        magnet = strike.get_first_torrent_magnet()
        results = {'magnet': magnet}
        self.download(results)

    def tms_search(self):
        search = TorrentMediaSearcher
        if self.season is None and self.episode is None:
            search.request_movie_magnet('torrentproject', self.name,
                                        callback=self.download,
                                        quality=self.quality)
        else:
            if self.quality is None:
                quality = 'normal'
            else:
                quality = self.quality
            search.request_tv_magnet(provider='eztv', show=self.name,
                                     season=int(self.season),
                                     episode=int(self.episode),
                                     quality=quality, callback=self.download)
