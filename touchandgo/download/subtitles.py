import logging

from os.path import join

from babelfish import Language
from guessit import guessit
from subliminal import download_best_subtitles, save_subtitles
from subliminal.subtitle import get_subtitle_path
from subliminal.video import Video

from touchandgo.helpers import get_settings


log = logging.getLogger('touchandgo.download')


class SubtitleDownloader(object):
    def __init__(self, sub_lang):
        self.lang = sub_lang

    def download(self, video_file):
        subtitle = None
        settings = get_settings()
        download_dir = settings.save_path
        log.info("Downloading subtitle")
        filepath = join(download_dir, video_file[0])
        guess = guessit(filepath)
        video = Video.fromguess(filepath, guess)
        video.size = video_file[1]
        try:
            subtitles = download_best_subtitles([video], {Language(self.lang)},
                                                only_one=True)
        except ValueError:
            pass
        if subtitles is not None and len(subtitles):
            subs = subtitles.values()[0]
            if len(subs):
                save_subtitles(video, subs, single=True)
                subtitle = get_subtitle_path(video.name, None)

        log.info("video_file: %s, filepath: %s, guess: %s, video: %s, "
                 "subtitle: %s", video_file, filepath, guess, video, subtitle)
        return subtitle

