from os.path import join
from time import sleep

from babelfish import Language
from libtorrent import add_magnet_uri, session
from guessit import guess_video_info
from subliminal import download_best_subtitles
from subliminal.subtitle import get_subtitle_path
from subliminal.video import Video


TMP_DIR = "/tmp"


def get_subtitle(magnet, lang):
    print("Obtaining subtitle")
    lt_session = session()
    params = {"save_path": TMP_DIR,
              "allocation": "compact"}
    handle = add_magnet_uri(lt_session, magnet, params)

    while (not handle.has_metadata()):
        sleep(.1)
    info = handle.get_torrent_info()
    files = info.files()

    biggest_file = ("", 0)

    for file_ in files:
        if file_.size > biggest_file[1]:
            biggest_file = [file_.path, file_.size]

    print("Guessing data")
    filepath = join(TMP_DIR, biggest_file[0])
    guess = guess_video_info(filepath, info=['filename'])
    video = Video.fromguess(filepath, guess)
    video.size = biggest_file[1]
    print("Donwloading Subtitle")
    subtitle = download_best_subtitles([video], {Language(lang)}, single=True)
    if not len(subtitle):
        subtitle = None
    else:
        subtitle = get_subtitle_path(join(TMP_DIR, video.name))

    lt_session.remove_torrent(handle)
    return subtitle
