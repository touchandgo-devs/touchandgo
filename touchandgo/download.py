import thread

from os import system, _exit
from os.path import join
from time import sleep
from datetime import datetime

from babelfish import Language
from guessit import guess_video_info
from libtorrent import add_magnet_uri, session
from subliminal import download_best_subtitles
from subliminal.subtitle import get_subtitle_path
from subliminal.video import Video

from touchandgo.constants import STATES
from touchandgo.helpers import is_port_free, get_free_port
from touchandgo.settings import DEBUG, TMP_DIR
from touchandgo.stream_server import serve_file


class DownloadManager(object):
    def __init__(self, magnet, port=None, sub_lang=None, serve=False):
        self.magnet = magnet
        if port is None:
            port = 8888
        port = int(port)
        if not is_port_free(port):
            port = get_free_port()

        self.port = port
        self.sub_lang = sub_lang
        self.serve = serve

        # number of pieces to wait until start streaming
        self.piece_st = 4
        # we are waiting untill all the first peices are downloaded
        self.holding_stream = True
        # the biggest file which is supposed to be a video file
        self._video_file = None
        self.callback = serve_file

        self.init_handle()

    def init_handle(self):
        params = {
            "save_path": TMP_DIR,
            #"allocation": "compact"
            }
        self.session = session()
        self.handle = add_magnet_uri(self.session, str(self.magnet), params)

    def start(self):
        self.start_time = datetime.now()
        print("Downloading metadata")
        while not self.handle.has_metadata():
            sleep(.1)
        print("Starting download")
        self.session.listen_on(6881, 6891)
        self.session.start_dht()

        chunks_strat = self.initial_strategy()

        try:
            while True:
                if not self.handle.is_seed():
                    self.strategy_master(chunks_strat)
                elif self.holding_stream:
                    self.holding_stream = False
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
        if self.sub_lang is not None:
            subtitle = self.get_subtitle()
            if subtitle is not None:
                command += " --sub-file %s" % subtitle
        try:
            system(command)
        except KeyboardInterrupt:
            pass
        _exit(0)

    def strategy_master(self, chunks_strat):
        status = self.handle.status()
        pieces = status.pieces
        first_n = pieces[:self.piece_st]

        if all(first_n):
            self.handle.set_sequential_download(False)
            pieces_strat = pieces[self.piece_st:self.piece_st + chunks_strat]
            if self.holding_stream or all(pieces_strat):
                if not self.holding_stream:
                    self.piece_st += chunks_strat
                else:
                    if self.callback is not None:
                        self.stream_video()

                for i in range(self.piece_st, self.piece_st + chunks_strat):
                    self.handle.piece_priority(i, 7)
                    self.handle.set_piece_deadline(i, 10000)

                for i in range(self.piece_st+chunks_strat,
                               self.piece_st + chunks_strat*2):
                    self.handle.piece_priority(i, 5)
                    self.handle.set_piece_deadline(i, 20000)
                self.holding_stream = False

    def stream_video(self):
        thread.start_new_thread(self.callback, (self, ))
        if not self.serve:
            thread.start_new_thread(self.run_vlc, ())

    def defrag(self):
        status = self.handle.status()
        numerales = ""
        for i, piece in enumerate(status.pieces):
            numeral = "#" if piece else " "
            numeral += str(self.handle.piece_priority(i))
            numerales += numeral
        print(numerales)

    def stats(self):
        status = self.handle.status()
        print '%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
            (status.progress * 100, status.download_rate / 1000,
             status.upload_rate / 1000, status.num_peers, STATES[status.state])
        print "Elapsed Time", datetime.now() - self.start_time

    def initial_strategy(self):
        self.handle.set_sequential_download(True)
        status = self.handle.status()

        for i in range(self.piece_st):
            self.handle.piece_priority(i, 7)
            self.handle.set_piece_deadline(i, 10000)

        """
        last_piece = len(status.pieces) - 1
        for i in range(last_piece-1, last_piece+1):
            self.handle.piece_priority(i, 7)
            self.handle.set_piece_deadline(i, 10000)
        """

        return len(status.pieces) / 25

    def get_subtitle(self):
        print("Downloading subtitle")
        video_file = self.video_file
        filepath = join(TMP_DIR, video_file[0])
        guess = guess_video_info(filepath, info=['filename'])
        video = Video.fromguess(filepath, guess)
        video.size = video_file[1]
        subtitle = download_best_subtitles([video], {Language(self.sub_lang)},
                                           single=True)
        if not len(subtitle):
            subtitle = None
        else:
            subtitle = get_subtitle_path(join(TMP_DIR, video.name))
        return subtitle

