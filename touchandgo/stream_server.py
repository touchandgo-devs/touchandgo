"""
http range detection based on
 https://github.com/menboku/musicsharer/blob/master/HTTPRangeServer.py
"""
import re
import logging

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

from json import dumps
from os import fstat
from time import sleep

from touchandgo.constants import STATES
from touchandgo.settings import WAIT_FOR_IT


log = logging.getLogger('touchandgo.stream_server')


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        pass


class VideoHandler(SimpleHTTPRequestHandler):
    manager = None

    def handle_one_request(self, *args, **kwargs):
        try:
            return SimpleHTTPRequestHandler.handle_one_request(self, *args,
                                                               **kwargs)
        except:
            pass

    def status(self):
        log.debug("returning 200 code")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        manager = self.manager
        dict_ = {"file": manager.video_file,
                 "elapsed": manager.elapsed_time(),
                 "rates": manager.rates(),
                 "state": STATES[manager.status.state],
                 "peers": manager.status.num_peers,
                 "streaming": manager.streaming}
        data = dumps(dict_)
        self.wfile.write(data)

    def do_GET(self):

        if self.path == "/status":
            self.status()
        else:
            f = self.send_head()
            if f:
                if self.range_from is not None and self.range_to is not None:
                    self.copy_chunk(f, self.wfile)
                else:
                    self.copyfile(f, self.wfile)
                f.close()

    def copy_chunk(self, in_file, out_file):
        def get_piece_length():
            info = self.manager.handle.get_torrent_info()
            length = info.piece_length()
            return length

        def get_blocks_for_range(range_from, range_to):
            length = get_piece_length()
            block_from = self.range_from / length
            block_to = self.range_to / length
            return block_from, block_to

        def is_block_available(block_number):
            status = self.manager.handle.status()
            pieces = status.pieces
            return all(pieces[block_number:block_number+3])

        in_file.seek(self.range_from)
        length = get_piece_length()

        bytes_copied = 0
        blocks = get_blocks_for_range(self.range_from, self.range_to)
        for block_number in range(blocks[0], blocks[1]+1):
            if not is_block_available(block_number):
                log.debug("requesting block %s" % block_number)
                self.manager.strategy.block_requested(block_number)
                sleep(WAIT_FOR_IT)

            while not is_block_available(block_number):
                sleep(WAIT_FOR_IT)
            self.manager.block_served(block_number)
            read_buf = in_file.read(length)
            if len(read_buf) == 0:
                break
            out_file.write(read_buf)
            bytes_copied += len(read_buf)
        return bytes_copied

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.


        """
        path = self.manager.get_video_path()
        try:
            # Always read in binary mode. Opening files in text mode may
            # cause newline translations, making the actual size of the
            # content transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None

        fs = fstat(f.fileno())
        total_length = fs[6]
        try:
            self.range_from, self.range_to = parse_range_header(
                self.headers.getheader("Range"), total_length)
        except InvalidRangeHeader:
            # Just serve them the whole file, although it's possibly
            # more correct to return a 4xx error?
            log.warning("Range header parsing failed, "
                            "serving complete file")
            self.range_from = self.range_to = None

        if self.range_from is not None or self.range_to is not None:
            log.debug("returning 206 code")
            self.send_response(206)
        else:
            log.debug("returning 200 code")
            self.send_response(200)
            self.send_header("Accept-Ranges", "bytes")
        guess = self.manager.guess(path)
        self.send_header("Content-Type", guess['mimetype'])
        log.debug("mime type is %s" % guess['mimetype'])
        log.debug("range %s to %s" % (self.range_from, self.range_to))
        if self.range_from is not None or self.range_to is not None:
            # TODO: Should also check that range is within the file size
            self.send_header("Content-Range",
                             "bytes %d-%d/%d" % (self.range_from,
                                                 self.range_to,
                                                 total_length))
            # Add 1 because ranges are inclusive
            self.send_header("Content-Length",
                             (1 + self.range_to - self.range_from))
        else:
            self.send_header("Content-Length", str(total_length))
        self.send_header("Last-Modified",
                         self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def finish(self, *args, **kwargs):
        try:
            if not self.wfile.closed:
                self.wfile.flush()
                self.wfile.close()
        except Exception:
            pass
        self.rfile.close()


class InvalidRangeHeader(Exception):
    pass


def serve_file(manager):
    print("serving on http://localhost:%s" % manager.port)
    log.info("serving on http://localhost:%s" % manager.port)
    server_address = ('0.0.0.0', manager.port)
    httpd = ThreadedHTTPServer(server_address, VideoHandler)
    manager.httpd = httpd
    VideoHandler.manager = manager
    httpd.serve_forever()


def parse_range_header(range_header, total_length):
    """
    Return a 2-element tuple containing the requested range offsets
    in bytes.
    - range_header is the HTTP header sans the "Range:" prefix
    - total_length is the length in bytes of the requested resource
      (needed to calculate offsets for a 'n bytes from the end' request
    If no Range explicitly requested, returns (None, None)
    If Range header could not be parsed, raises InvalidRangeHeader
    (which could either be handled as a user
    request failure, or the same as if (None, None) was returned
    """
    if range_header is None or range_header == "":
        return (None, None)
    if not range_header.startswith("bytes="):
        log.error("Don't know how to parse Range: %s [1]" %
                  (range_header))
        raise InvalidRangeHeader("Don't know how to parse non-bytes Range: %s" %
                                 (range_header))
    regex = re.compile(r"^bytes=(\d*)\-(\d*)$")
    rangething = regex.search(range_header)
    if rangething:
        r1 = rangething.group(1)
        r2 = rangething.group(2)
        log.debug("Requested range is [%s]-[%s]" % (r1, r2))

        if r1 == "" and r2 == "":
            log.warning("Requested range is meaningless")
            raise InvalidRangeHeader("Requested range is meaningless")

        if r1 == "":
            # x bytes from the end of the file
            try:
                final_bytes = int(r2)
            except ValueError:
                raise InvalidRangeHeader("Invalid trailing range")
            return (total_length-final_bytes, total_length - 1)

        try:
            from_val = int(r1)
        except ValueError:
            raise InvalidRangeHeader("Invalid starting range value")
        if r2 != "":
            try:
                end_val = int(r2)
            except ValueError:
                raise InvalidRangeHeader("Invalid ending range value")
            return (from_val, end_val)
        else:
            return (from_val, total_length - 1)
    else:
        raise InvalidRangeHeader("Don't know how to parse Range: %s" %
                                 (range_header))
