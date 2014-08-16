import logging

from os.path import join

from babelfish import Language
from guessit import guess_video_info
from subliminal import download_best_subtitles
from subliminal.subtitle import get_subtitle_path
from subliminal.video import Video

from touchandgo.settings import TMP_DIR


log = logging.getLogger('touchandgo.download')


class SubtitleDownloader(object):
    def __init__(self, sub_lang):
        self.lang = sub_lang

    def download(self, video_file):
        print("Downloading subtitle")
        log.info("Downloading subtitle")
        filepath = join(TMP_DIR, video_file[0])
        guess = guess_video_info(filepath, info=['filename'])
        video = Video.fromguess(filepath, guess)
        video.size = video_file[1]
        subtitle = download_best_subtitles([video], {Language(self.lang)},
                                           single=True)
        if not len(subtitle):
            subtitle = None
        else:
            subtitle = get_subtitle_path(join(TMP_DIR, video.name))
        log.info("video_file: %s, filepath: %s, guess: %s, video: %s"
                 "subtitle: %s", video_file, filepath, guess, video, subtitle)
        return subtitle

