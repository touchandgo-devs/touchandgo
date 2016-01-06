#! /usr/bin/env python2
import argparse
import logging
import sys

from babelfish import Language
from blessings import Terminal
from libtorrent import version as libtorrent_version

from touchandgo.helpers import daemonize
from touchandgo.logger import log_set_up
from touchandgo.search import SearchAndStream


log = logging.getLogger('touchandgo.main')


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
                        help="Player to use. vlc|omxplayer|chromecast")
    parser.add_argument("--search", default=None,
                        help="search lib to use (options are 'kat', 'tms', 'strike')")
    parser.add_argument("--nocache", action="store_false", default=True,
                        help="Search for the torrent again"),

    args = parser.parse_args()

    log_set_up(args.verbose)
    log.info("Starting touchandgo")
    log.debug("Running Python %s on %r", sys.version_info, sys.platform)
    log.debug("Libtorrent version: %s", libtorrent_version)

    try:
        if args.sub is not None:
            Language(args.sub)

        touchandgo = SearchAndStream(args.name, season=args.season_number,
                                     episode=args.episode_number,
                                     sub_lang=args.sub, serve=args.serve,
                                     quality=args.quality, port=args.port,
                                     player=args.player, search=args.search,
                                     use_cache=args.nocache)
        if args.daemon:
            def callback():
                touchandgo.serve = True
                touchandgo.watch()
            daemonize(args, callback)
        else:
            term = Terminal()
            with term.fullscreen():
                touchandgo.watch()
    except ValueError as e:
        print(e)

if __name__ == '__main__':
    main()
