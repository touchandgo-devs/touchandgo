import thread
import libtorrent as lt
import logging

from os import system, _exit
from time import sleep
from datetime import datetime

from libtorrent import add_magnet_uri, session

from touchandgo.constants import STATES
from touchandgo.helpers import is_port_free, get_free_port
from touchandgo.settings import DEBUG, TMP_DIR
from touchandgo.strategy import DefaultStrategy
from touchandgo.stream_server import serve_file
from touchandgo.subtitles import SubtitleDownloader


log = logging.getLogger('touchandgo.download')


class DownloadManager(object):
    strategy_class = DefaultStrategy
    sub_downloader_class = SubtitleDownloader

    def __init__(self, magnet, port=None, sub_lang=None, serve=False):
        log.info("[Magnet]: %s [Port]: %s [Sub_lang]: %s [Serve]: %s ",
                 magnet, port, sub_lang, serve)
        self.magnet = magnet
        if port is None:
            port = 8888
        port = int(port)
        if not is_port_free(port):
            port = get_free_port()

        self.port = port
        self.serve = serve

        # number of pieces to wait until start streaming
        # we are waiting untill all the first peices are downloaded
        # the biggest file which is supposed to be a video file
        self._video_file = None
        self.callback = serve_file
        self._served_blocks = None

        self.init_handle()
        self.strategy = self.strategy_class(self)

        if sub_lang is not None:
            self.subtitle = self.sub_downloader_class(sub_lang)
        else:
            self.subtitle = None

    def init_handle(self):
        params = {
            "save_path": TMP_DIR,
            "allocation": lt.storage_mode_t.storage_mode_sparse,
            }
        self.session = session()
        print self.magnet
        self.handle = add_magnet_uri(self.session, str(self.magnet), params)

    def start(self):
        self.start_time = datetime.now()
        self.session.listen_on(6881, 6891)
        self.session.start_dht()
        print("Downloading metadata")
        log.info("Downloading metadata")
        while not self.handle.has_metadata():
            sleep(.1)
        log.info("Starting download")

        try:
            while True:
                if not self.handle.is_seed():
                    self.strategy.master()
                elif self.strategy.holding_stream:
                    self.strategy.holding_stream = False
                    self.stream_video()
                print("\n" * 80)
                if DEBUG:
                    self.defrag()
                self.stats()
                sleep(1)
        except KeyboardInterrupt:
            _exit(0)

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

    def run_vlc(self):
        command = "vlc http://localhost:%s -q" % self.port
        if self.subtitle is not None:
            subtitle = self.subtitle.download(self.video_file)
            if subtitle is not None:
                command += " --sub-file %s" % subtitle
        try:
            system(command)
        except KeyboardInterrupt:
            pass
        _exit(0)

    def stream(self):
        if self.callback is not None:
            status = self.handle.status()
            pieces = status.pieces
            self._served_blocks = [False for i in range(len(pieces))]
            thread.start_new_thread(self.callback, (self, ))
            if not self.serve:
                thread.start_new_thread(self.run_vlc, ())

    def block_served(self, block):
        self._served_blocks[block] = True

    def defrag(self):
        status = self.handle.status()
        numerales = ""
        for i, piece in enumerate(status.pieces):
            numeral = "#" if piece else " "
            if self._served_blocks is not None and self._served_blocks[i]:
                numeral = ">"
            numeral += str(self.handle.piece_priority(i))
            numerales += numeral
        print(numerales)




    def stats(self):
        status = self.handle.status()
        print '%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
            (status.progress * 100, status.download_rate / 1000,
             status.upload_rate / 1000, status.num_peers, STATES[status.state])
        print "Elapsed Time", datetime.now() - self.start_time

