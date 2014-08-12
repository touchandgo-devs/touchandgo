import BaseHTTPServer

from os.path import join

from guessit import guess_video_info

from touchandgo.settings import TMP_DIR


def serve_file(manager):

    class HTTPHandlerOne(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            video = manager.video_file
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
