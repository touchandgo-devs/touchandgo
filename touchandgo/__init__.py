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
                 serve=False, quality=None, port=None, cast=False):
        self.name = name
        self.season = season
        self.episode = episode
        self.sub_lang = sub_lang
        self.serve = serve
        self.quality = quality
        self.port = port
        self.do_cast = cast

    def download(self, results):
        log.info("Processing magnet link")
        magnet = results['magnet']
        log.info("Magnet: %s", magnet)
        manager = DownloadManager(magnet, port=self.port, serve=self.serve,
                                  sub_lang=self.sub_lang, cast=self.do_cast)
        manager.start()
        set_config_dir()

        history = History(date=int(time()), name=self.name, season=self.season,
                          episode=self.episode)
        history.save()
        history.update()

    def watch(self):
        try:
            if self.name[:6] == 'magnet':
                results = {'magnet': self.name}
                print results
                self.download(results)
            else:
                self.search_magnet()
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
            search.request_tv_magnet(provider='eztv', show=self.name,
                                     season=int(self.season),
                                     episode=int(self.episode),
                                     quality=quality, callback=self.download)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")

    parser.add_argument("sea_ep", nargs='*', default=[None, None])
    parser.add_argument("--sub", nargs='?', default=None)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--quality", nargs='?', default=None)
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--port", "-p", default="8888")
    parser.add_argument("--season", action="store_true")
    parser.add_argument("--verbose", action="store_true", default=None)
    parser.add_argument("--cast", action="store_true", default=False)

    args = parser.parse_args()

    log_set_up(args.verbose)
    log.info("Starting touchandgo")
    log.info("Running Python %s on %r", sys.version_info, sys.platform)
    log.info("Libtorrent version: %s", libtorrent_version)

    episode = int(args.sea_ep[1]) if args.sea_ep[1] is not None else None
    touchandgo = SearchAndStream(args.name, season=args.sea_ep[0],
                                 episode=episode, sub_lang=args.sub,
                                 serve=args.serve, quality=args.quality,
                                 port=args.port, cast=args.cast)
    if args.daemon:
        daemonize(args, touchandgo.watch)
    else:
        play_next_episode = True
        while play_next_episode:
            touchandgo.watch()
            touchandgo.episode += 1
            play_next_episode = args.season

if __name__ == '__main__':
    main()
