from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from os.path import join

from guessit import guess_video_info

from touchandgo.settings import TMP_DIR

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        pass

def serve_file(manager):

    class VideoHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            video = manager.video_file
            video_path = join(TMP_DIR, video[0])
            self.send_response(200)
            guess = guess_video_info(video_path, info=['filename'])
            #import mimetypes
            #print mimetypes.read_mime_types(video_path)
            #print guess
            self.send_header('Content-type', guess["mimetype"])
            self.send_header('Mime-type', guess["mimetype"])
            self.end_headers()
            data = open(video_path).read()
            self.wfile.write(data)

    def run(server_class=ThreadedHTTPServer,
            handler_class=BaseHTTPRequestHandler):
        server_address = ('0.0.0.0', manager.port)
        httpd = server_class(server_address, handler_class)
        httpd.serve_forever()

    run(handler_class=VideoHandler)
