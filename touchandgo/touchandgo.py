import argparse

from fabric.operations import local
from torrentmediasearcher import TorrentMediaSearcher
from subtitles import get_subtitle


def main(name, season, episode):
    print("Obteniendo magnet")
    search = TorrentMediaSearcher()
    search.request_tv_magnet(provider='eztv', show=name , season=season,
                             episode=episode, quality='normal',
                             callback=get_magnet)

def get_magnet(results):
    magnet = results['magnet']
    subtitle = get_subtitle(magnet)
    command = "peerflix \"%s\" -t /tmp/%s --vlc" % (magnet, subtitle)
    local(command, capture=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("season")
    parser.add_argument("episode")
    args = parser.parse_args()

    main(args.name, int(args.season), int(args.episode))
