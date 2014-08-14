#! /usr/bin/env python
import argparse

from time import time
from torrentmediasearcher import TorrentMediaSearcher

from touchandgo.helpers import daemonize, set_config_dir
from touchandgo.history import History
from touchandgo.download import DownloadManager


def watch(name, season=None, episode=None, sub_lang=None, serve=False,
          quality=None, port=None):

    def get_magnet(results):
        print("Processing magnet link")
        magnet = results['magnet']
        print(magnet)
        manager = DownloadManager(magnet, port=port, serve=serve,
                                  sub_lang=sub_lang)
        manager.start()
        set_config_dir()

        history = History(date=int(time()), name=name, season=season,
                          episode=episode)
        history.save()
        history.update()

    print("Searching torrent")
    search = TorrentMediaSearcher
    if season is None and episode is None:
        search.request_movie_magnet('torrentproject', name,
                                    callback=get_magnet, quality=quality)
    else:
        if quality is None:
            quality = 'normal'
        search.request_tv_magnet(provider='eztv', show=name,
                                 season=int(season), episode=int(episode),
                                 quality=quality, callback=get_magnet)

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
    args = parser.parse_args()

    if args.daemon:
        daemonize(args, watch)
    else:
        episode = int(args.sea_ep[1]) if args.sea_ep[1] is not None else None
        play_next_episode = True
        while play_next_episode:
            watch(args.name, season=args.sea_ep[0], episode=episode,
                  sub_lang=args.sub, serve=args.serve, quality=args.quality,
                  port=args.port)
            episode += 1
            play_next_episode = args.season

if __name__ == '__main__':
    main()
