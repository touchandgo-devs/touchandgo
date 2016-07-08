import logging

import pychromecast

from blessings import Terminal
from os import system
from time import sleep

from touchandgo.helpers import get_interface


log = logging.getLogger('touchandgo.output')


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
        log.debug("VLC command: %s" % command)
        system(command)

    def _player(self):
        return ""

    def _subs(self):
        return ""


class VLCOutput(Output):
    def _player(self):
        command = "vlc %s -q" % self.stream_url
        return command

    def _subs(self):
        subs = "--sub-file \"%s\"" % self.sub_file
        return subs


class OMXOutput(Output):
    def _player(self):
        return "omxplayer --live --timeout 360 -p -o hdmi %s" \
            % self.stream_url

    def _subs(self):
        subs = "--subtitle %s" % self.sub_file
        return subs


class CastOutput(Output):
    @classmethod
    def select_chromecast(cls):
        name = None
        chromecasts = pychromecast.get_chromecasts_as_dict().keys()

        if not chromecasts:
            return

        if len(chromecasts) > 1:
            term = Terminal()

            print(term.clear())
            print(term.bold("Touchandgo\n"))
            print(term.red("Chromecasts Availables"))
            for i, cc_name in enumerate(chromecasts, 1):
                option = term.cyan("%s) " % i)
                option += cc_name
                print(option)

            input_text = "Select which chromecast you want to cast (1-%d): " % \
                len(chromecasts)
            user_input = raw_input(input_text)

            try:
                opt = int(user_input) - 1
                if opt > len(chromecasts) or opt < 1:
                    opt = 0
            except ValueError:
                opt = 0

            name = chromecasts[opt]
        elif len(chromecasts) == 1:
            name = chromecasts[0]

        return name

    def run(self):
        chromecast = self.parent.chromecast
        device = pychromecast.get_chromecast(friendly_name=chromecast)
        interface = get_interface()
        guess = self.parent.guess(self.parent.get_video_path())
        device.play_media("http://%s:%s" % (interface, self.parent.port),
                          guess['mimetype'])
        while True:
            sleep(1)

    def __del__(self):
        self.chromecast.media_controller.stop()
