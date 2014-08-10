import BaseHTTPServer
import thread

from os import system
from os.path import join
from time import sleep
from datetime import datetime

from babelfish import Language
from guessit import guess_video_info
from libtorrent import add_magnet_uri, session
from subliminal import download_best_subtitles
from subliminal.subtitle import get_subtitle_path
from subliminal.video import Video


TMP_DIR = "/tmp"


class DownloadManager(object):
    def __init__(self, magnet, port=None, sub_lang=None, serve=False):
        self.start_time = datetime.now()
        self.session = session()
        self.piece_st = 4
        self.first_pieces = True
        if port is not None:
            port = 8888
        self.port = port
        self.callback = serve_file
        self.serve = serve
        self.sub_lang = sub_lang

        params = {"save_path": TMP_DIR,
                  "allocation": "compact"}
        self.handle = add_magnet_uri(self.session, magnet, params)
        self.states = ['queued', 'checking', 'downloading metadata',
                       'downloading', 'finished', 'seeding', 'allocating']

    def start(self):
        print("Downloading metadata")
        while not self.handle.has_metadata():
            sleep(.1)
        print("Starting download")
        self.session.listen_on(6881, 6891)
        self.session.start_dht()

        chunks_strat = self.initial_strategy()

        for i in range(self.piece_st):
            self.handle.piece_priority(i, 7)
            self.handle.set_piece_deadline(i, 10000)

        while True:
            if not self.handle.is_seed():
                self.strategy_master(chunks_strat)
            print "\n" * 50
            #self.defrag()
            self.stats()
            sleep(1)

    def get_biggest_file(self):
        info = self.handle.get_torrent_info()
        biggest_file = ("", 0)
        files = info.files()
        for file_ in files:
            if file_.size > biggest_file[1]:
                biggest_file = [file_.path, file_.size]

        return biggest_file

    def run_vlc(self):
        command = "vlc http://localhost:%s" % self.port
        if self.sub_lang is not None:
            subtitle = self.get_subtitle()
            if subtitle is not None:
                command += " --sub-file %s" % subtitle
        system(command)

    def strategy_master(self, chunks_strat):
        status = self.handle.status()
        pieces = status.pieces
        first_n = pieces[:self.piece_st]

        if all(first_n):
            self.handle.set_sequential_download(False)
            pieces_strat = pieces[self.piece_st:self.piece_st + chunks_strat]
            if self.first_pieces or all(pieces_strat):
                if not self.first_pieces:
                    self.piece_st += chunks_strat
                else:
                    if self.callback is not None:
                        thread.start_new_thread(self.callback, (self, ))
                        if not self.serve:
                            thread.start_new_thread(self.run_vlc, ())

                for i in range(self.piece_st, self.piece_st + chunks_strat):
                    self.handle.piece_priority(i, 7)
                    self.handle.set_piece_deadline(i, 10000)

                for i in range(self.piece_st+chunks_strat,
                               self.piece_st + chunks_strat*2):
                    self.handle.piece_priority(i, 5)
                    self.handle.set_piece_deadline(i, 20000)
                self.first_pieces = False

    def defrag(self):
        status = self.handle.status()
        numerales = ""
        for i, piece in enumerate(status.pieces):
            numeral = "#" if piece else " "
            numeral += str(self.handle.piece_priority(i))
            numerales += numeral
        print numerales

    def stats(self):
        status = self.handle.status()
        print '%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
            (status.progress * 100, status.download_rate / 1000,
             status.upload_rate / 1000, status.num_peers,
             self.states[status.state])
        print "Elapsed Time", datetime.now() - self.start_time

    def initial_strategy(self):
        self.handle.set_sequential_download(True)
        status = self.handle.status()
        return len(status.pieces) / 25

    def get_subtitle(self):
        print("Downloading subtitle")
        video_file = self.get_biggest_file()
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

def get_file(filename):
    try:
        src = join(TMP_DIR, filename)
        data = open(src).read()
        return data
    except IOError as exc:
        return str(exc)

def serve_file(manager):

    class HTTPHandlerOne(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            video = manager.get_biggest_file()
            video_path = join(TMP_DIR, video[0])
            self.send_response(200)
            guess = guess_video_info(video_path, info=['filename'])
            self.send_header('Content-type', guess["mimetype"])
            self.send_header('Mime-type', guess["mimetype"])
            self.end_headers()
            self.wfile.write(open(video_path).read())

    def run(server_class=BaseHTTPServer.HTTPServer,
            handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
        server_address = ('', manager.port)
        httpd = server_class(server_address, handler_class)
        httpd.serve_forever()

    run(handler_class=HTTPHandlerOne)
