#! /usr/bin/env python2
import argparse
import logging
import sys

from os import _exit
from time import time
from torrentmediasearcher import TorrentMediaSearcher

from libtorrent import version as libtorrent_version
from touchandgo.helpers import daemonize, set_config_dir
from touchandgo.history import History
from touchandgo.download import DownloadManager
from touchandgo.logger import log_set_up


log = logging.getLogger('touchandgo.main')


class SearchAndStream(object):
    def __init__(self, name, season=None, episode=None, sub_lang=None,
                 serve=False, quality=None, port=None, player=None):
        self.name = name
        self.season = season
        self.episode = episode
        self.sub_lang = sub_lang
        self.serve = serve
        self.quality = quality
        self.port = port
        self.player = player

        set_config_dir()

    def download(self, results):
        log.info("Processing magnet link")
        magnet = results['magnet']
        log.info("Magnet: %s", magnet)

        set_config_dir()

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


def main():
    parser = argparse.ArgumentParser(
        description="Command line tool to watch torrents")
    parser.add_argument("name", help="The name of the series or movie")

    parser.add_argument("season_number", default=None, nargs="?", type=int,
                        help="Season number")
    parser.add_argument("episode_number", default=None, nargs="?", type=int,
                        help="Episode number")
    parser.add_argument("--sub", nargs='?', default=None,
                        help="Subtitle language")
    parser.add_argument("--serve", action="store_true",
                        help="Do not run VLC")
    parser.add_argument("--quality", nargs='?', default=None,
                        help="quality of the video [normal|hd|fullhd]")
    parser.add_argument("--daemon", action="store_true",
                        help="Daemonize the process"),
    parser.add_argument("--port", "-p", default="8888",
                        help="The port where the stream will be served")
    parser.add_argument("--verbose", action="store_true", default=None,
                        help="Show _all_ the logs")
    parser.add_argument("--player", default='vlc',
                        help="Player to use. vlc|omxplayer")

    args = parser.parse_args()

    log_set_up(args.verbose)
    log.info("Starting touchandgo")
    log.debug("Running Python %s on %r", sys.version_info, sys.platform)
    log.debug("Libtorrent version: %s", libtorrent_version)

    touchandgo = SearchAndStream(args.name, season=args.season_number,
                                 episode=args.episode_number,
                                 sub_lang=args.sub, serve=args.serve,
                                 quality=args.quality, port=args.port,
                                 player=args.player)
    if args.daemon:
        def callback():
            touchandgo.serve = True
            touchandgo.watch()
        daemonize(args, callback)
    else:
        touchandgo.watch()

if __name__ == '__main__':
    main()
