"""
http range detection based on
 https://github.com/menboku/musicsharer/blob/master/HTTPRangeServer.py
"""
import re
import logging

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

from os import fstat
from os.path import join
from time import sleep

from guessit import guess_video_info

from touchandgo.settings import TMP_DIR, WAIT_FOR_IT


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

    def do_GET(self):
        f = self.send_head()
        if f:
            if self.range_from is not None and self.range_to is not None:
                self.copy_chunk(f, self.wfile)
            else:
                self.copyfile(f, self.wfile)
            f.close()

    def get_video_path(self):
        video = self.manager.video_file
        video_path = join(TMP_DIR, video[0])
        return video_path

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
        #print "getting blocks", blocks
        for block_number in range(blocks[0], blocks[1]+1):
            if not is_block_available(block_number):
                #print "requesting block", block_number
                self.manager.strategy.block_requested(block_number)
                sleep(WAIT_FOR_IT)

            while not is_block_available(block_number):
                #print "sleeping"
                sleep(WAIT_FOR_IT)
            #print "returning block", block_number
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
        path = self.get_video_path()
        print path
        try:
            # Always read in binary mode. Opening files in text mode may
            # cause newline translations, making the actual size of the
            # content transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            print "OOPS"
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
            self.send_response(206)
        else:
            self.send_header("Accept-Ranges", "bytes")
            self.send_response(200)
        guess = guess_video_info(path, info=['filename'])
        self.send_header("Content-Type", guess['mimetype'])
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
    # range_header = self.headers.getheader("Range")
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
