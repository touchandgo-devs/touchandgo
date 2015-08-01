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
    def select_chromecast(self):
        import pychromecast

        self.chromecast = None
        chromecasts = pychromecast.get_chromecasts_as_dict().keys()

        if not chromecasts:
            return

        if len(chromecasts) > 1:
            from blessings import Terminal
            term = Terminal()

            print(term.clear())
            print(term.bold("Touchandgo\n"))
            print(term.red("Chromecasts Availables"))
            for i, cc_name in enumerate(chromecasts, 1):
                option = term.cyan("%s) " % i)
                option += cc_name
                print(option)

            input_text = "Select which chromecast you want to play (1-%d): " % \
                len(chromecasts)
            user_input = raw_input(input_text)

        try:
            opt = int(user_input) - 1
            if opt > len(chromecasts) or opt < 1:
                opt = 0
        except ValueError:
            opt = 0

        self.chromecast = pychromecast.get_chromecast(
            friendly_name=chromecasts[opt])

    def run(self):
        self.select_chromecast()
        interface = get_interface()
        guess = self.parent.guess(self.parent.get_video_path())
        self.chromecast.play_media("http://%s:%s" % (interface, self.parent.port),
                                   guess['mimetype'])
        while True:
            sleep(1)

    def __del__(self):
        self.chromecast.media_controller.stop()
