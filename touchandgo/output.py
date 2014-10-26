from os import system
from time import sleep

from touchandgo.helpers import get_interface


class Output(object):
    def __init__(self, stream_url, sub_file, parent):
        self.stream_url = stream_url
        self.sub_file = sub_file
        self.parent = parent

    def run(self):
        player_command = self._player()
        if self.sub_file is not None:
            subs = self._subs()
        else:
            subs = ""

        command = "%s %s" % (player_command, subs)
        system(command)

    def _player(self):
        return ""

    def _subs(self):
        return ""


class VLCOutput(Output):
    def _player(self):
        return "vlc %s -q" % self.stream_url

    def _subs(self):
        subs = "--sub-file %s" % self.sub_file
        return subs


class OMXOutput(Output):
    def _player(self):
        return "omxplayer --live --timeout 360 -p -o hdmi %s" \
            % self.stream_url

    def _subs(self):
        subs = "--subtitle %s" % self.sub_file
        return subs

class CastOutput(Output):
    def run(self):
        import pychromecast

        self.chromecast = pychromecast.get_chromecast()
        interface = get_interface()
        guess = self.parent.guess(self.parent.get_video_path())
        self.chromecast.play_media("http://%s:%s" % (interface, self.parent.port),
                                   guess['mimetype'])
        while True:
            sleep(1)

    def __del__(self):
        self.chromecast.media_controller.stop()
