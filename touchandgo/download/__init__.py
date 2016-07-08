#! /usr/bin/env python2
from __future__ import division

import argparse
import thread
import logging

from os import _exit
from os.path import join, exists
from time import sleep
from datetime import datetime, timedelta

from blessings import Terminal
from colorama import Fore
from guessit import guessit
from libtorrent import add_magnet_uri, session, storage_mode_t

from touchandgo.constants import STATES
from touchandgo.download.strategy import DefaultStrategy
from touchandgo.download.subtitles import SubtitleDownloader
from touchandgo.helpers import is_port_free, get_free_port, get_settings
from touchandgo.logger import log_set_up
from touchandgo.output import VLCOutput, OMXOutput, CastOutput
from touchandgo.settings import DEBUG, WAIT_FOR_IT, DEFAULT_PORT
from touchandgo.stream_server import serve_file


log = logging.getLogger('touchandgo.download')
term = Terminal()


class DownloadManager(object):
    strategy_class = DefaultStrategy
    sub_downloader_class = SubtitleDownloader

    def __init__(self, magnet, port=None, sub_lang=None, serve=False,
                 player=None):
        self.settings = get_settings()
        self.magnet = magnet
        if port is None:
            port = DEFAULT_PORT
        port = int(port)
        if not is_port_free(port):
            port = get_free_port()

        log.info("[Magnet]: %s [Port]: %s [Sub_lang]: %s [Serve]: %s "
                 "[Player] %s ",
                 magnet, port, sub_lang, serve, player)

        self.port = port
        self.serve = serve
        if player is None:
            player = self.settings.players.default
        self.player = player

        # number of pieces to wait until start streaming
        # we are waiting untill all the first peices are downloaded
        # the biggest file which is supposed to be a video file
        self._video_file = None
        self.callback = serve_file
        self._served_blocks = None
        self.streaming = False

        self.stream_th = None
        self.player_th = None
        self.httpd = None
        self._guess = None

        self.init_handle()
        self.strategy = self.strategy_class(self)

        if sub_lang is not None:
            self.subtitle = self.sub_downloader_class(sub_lang)
        else:
            self.subtitle = None

    def init_handle(self):
        params = {
            "save_path": self.settings.save_path,
            "allocation": storage_mode_t.storage_mode_sparse,
            }
        self.session = session()
        self.handle = add_magnet_uri(self.session, str(self.magnet), params)

        up_limit = self.settings.limits.upload
        if up_limit:
            self.handle.set_upload_limit(up_limit)
        down_limit = self.settings.limits.download
        if down_limit:
            self.handle.set_download_limit(down_limit)

    @property
    def status(self):
        return self.handle.status()

    def start(self):
        try:
            self.start_time = datetime.now()
            self.session.listen_on(6881, 6891)
            self.session.start_dht()
            print("Downloading metadata")
            log.info("Downloading metadata")
            while not self.handle.has_metadata():
                print(term.clear())
                print(self.screen_data(DEBUG))
                elapsed_time = datetime.now() - self.start_time
                if elapsed_time > timedelta(minutes=2):
                    print("Torrent metadata not available")
                    return
                else:
                    sleep(.5)
            log.info("Starting download")
            self.strategy.initial()

            while True:
                is_seed = self.handle.is_seed()
                if not is_seed:
                    self.strategy.master()
                elif self.strategy.holding_stream:
                    self.strategy.holding_stream = False

                if not self.streaming and is_seed:
                    self.stream()

                print(term.clear())
                print(self.screen_data(DEBUG))
                sleep(1)
        except KeyboardInterrupt:
            if self.httpd is not None:
                self.httpd.shutdown()
            raise KeyboardInterrupt

    @property
    def video_file(self):
        if self._video_file is None:
            self._video_file = self.get_biggest_file()
            log.info("Video File: %s", self._video_file)
        return self._video_file

    def get_biggest_file(self):
        info = self.handle.get_torrent_info()
        biggest_file = ("", 0)
        files = info.files()
        for file_ in files:
            if file_.size > biggest_file[1]:
                biggest_file = [file_.path, file_.size]

        return biggest_file

    def wait_for_file(self):
        while not exists(join(self.settings.save_path, self.video_file[0])):
            sleep(WAIT_FOR_IT)

    def output(self, chromecast=None):
        self.chromecast = chromecast
        self.wait_for_file()
        stream_url = "http://localhost:%s" % self.port
        if self.subtitle is not None:
            subtitle = self.subtitle.download(self.video_file)
        else:
            subtitle = None

        players = {"vlc": VLCOutput,
                   "omxplayer": OMXOutput,
                   "chromecast": CastOutput
                   }
        output_class = players.get(self.player, VLCOutput)
        output = output_class(stream_url, subtitle, self)
        try:
            output.run()
        except KeyboardInterrupt:
            log.debug("Closing output thread")
        _exit(0)

    def stream(self):
        if self.callback is not None and not self.streaming:
            self.streaming = True
            pieces = self.status.pieces
            self._served_blocks = [False for i in range(len(pieces))]
            self.stream_th = thread.start_new_thread(self.callback, (self, ))
            if not self.serve:
                params = ()
                if self.player == "chromecast":
                    chromecast = CastOutput.select_chromecast()
                    params = (chromecast, )

                self.player_th = thread.start_new_thread(self.output, params)

    def block_served(self, block):
        self._served_blocks[block] = True

    def defrag(self):
        download_queue = self.handle.get_download_queue()
        downloading = [piece['piece_index'] for piece in download_queue]
        numerales = ""
        pieces = self.status.pieces
        for i, piece in enumerate(pieces):
            numeral = Fore.GREEN + "#" if piece else Fore.RED + "#"
            if i in downloading:
                numeral = Fore.YELLOW + "v"
            elif self._served_blocks is not None and self._served_blocks[i]:
                numeral = Fore.BLUE + ">"
            numeral += str(self.handle.piece_priority(i))
            numerales += numeral
        if numerales != "":
            numerales = term.magenta("\nPieces download state:\n" + numerales)
        return "%s\n" % numerales

    def screen_data(self, defrag=False):
        status = self.status
        text = Fore.WHITE
        text += term.bold('Touchandgo\n\n')
        text += STATES[status.state]
        text += term.yellow(' %.2f%% complete ' % (status.progress * 100))
        rates = self.rates()
        rate_text = '(down: %.1f kB/s up: %.1f kB/s peers: %d)\n' % \
                    (rates[0], rates[1], status.num_peers)
        text += term.green(rate_text)

        if defrag:
            text += self.defrag()
            text += Fore.WHITE
            text += "\n\n"

        if self._video_file is not None:
            text += term.white("Serving ")
            text += term.yellow(self.video_file[0])
            text += term.white(" on ")
            text += term.blue("http://localhost:%s\n") % self.port

        text += term.white("Elapsed Time: ")
        text += term.red(self.elapsed_time())
        text += "\n"
        return text

    def elapsed_time(self):
        return str(datetime.now() - self.start_time).split(".")[0]

    def rates(self):
        return self.status.download_rate / 1000, self.status.upload_rate / 1000

    def get_video_path(self):
        video = self.video_file
        video_path = join(self.settings.save_path, video[0])
        return video_path

    def guess(self, path):
        if self._guess is None:
            self._guess = guessit(path)
        return self._guess


def main():
    log_set_up()
    parser = argparse.ArgumentParser()

    parser.add_argument("magnet", nargs='?', default=None)
    parser.add_argument("--sub", nargs='?', default=None)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", "-p", default="8888")

    args = parser.parse_args()

    manager = DownloadManager(args.magnet, port=args.port, serve=args.serve,
                              sub_lang=args.sub)
    manager.start()

if __name__ == "__main__":
    main()
