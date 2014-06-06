#! /usr/bin/env python
import argparse
import socket

from torrentmediasearcher import TorrentMediaSearcher

from subtitles import get_subtitle
from subprocess import PIPE, STDOUT, Popen
import re


def get_free_port():
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('localhost', 0))
  addr, port = s.getsockname()
  s.close()
  return port


def execute(command):
    process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
    print("Running peerflix")
    while True:
        nextline = process.stdout.readline()
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', nextline)
        if len(urls):
            print("streaming url: %s" % urls[0])
            break

        if nextline == '' and process.poll() != None:
            break

    output = process.communicate()[0]
    exitCode = process.returncode
    print output, exitCode


def main(name, season=None, episode=None, sub_lang=None, serve=False,
         quality=None, random_port=False):

    def get_magnet(results):
        print("Processing magnet link")
        magnet = results['magnet']
        command = "peerflix \"%s\"" % magnet
        if sub_lang is not None:
            subtitle = get_subtitle(magnet, sub_lang)
            if subtitle is not None:
                command += " -t %s" % subtitle
        if random_port:
            command += " -p%s" % get_free_port()
        if not serve:
            command += " --vlc"

        print("executing command %s" % command)
        execute(command)

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("name")

    parser.add_argument("sea_ep", nargs='*', default=[None, None])
    parser.add_argument("--sub", nargs='?', default=None)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--quality", nargs='?', default=None)
    args = parser.parse_args()

    main(args.name, season=args.sea_ep[0], episode=args.sea_ep[1],
         sub_lang=args.sub, serve=args.serve, quality=args.quality)
