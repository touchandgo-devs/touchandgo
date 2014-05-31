from time import sleep

from babelfish import Language
from libtorrent import add_magnet_uri, session
from guessit import guess_video_info
from subliminal import download_best_subtitles
from subliminal.subtitle import get_subtitle_path
from subliminal.video import Video


def get_subtitle(magnet, lang):
    print("Explorando torrent")
    lt_session = session()
    params = {"save_path": "/tmp"}
    handle = add_magnet_uri(lt_session, magnet, params)
    print "esperando"
    while (not handle.has_metadata()):
        sleep(.1)
    print "esperando"
    info = handle.get_torrent_info()
    print "esperando", info
    files = info.files()

    biggest_file = ("", 0)

    for file_ in files:
        if file_.size > biggest_file[1]:
            biggest_file = [file_.path, file_.size]

    print("Adivinando data")
    filepath = biggest_file[0]
    guess = guess_video_info(filepath, info = ['filename'])
    video = Video.fromguess(filepath, guess)
    video.size = biggest_file[1]
    print("Bajando el subtitulo")
    subtitle = download_best_subtitles([video], {Language(lang)}, single=True)
    if not len(subtitle):
        subtitle = None
    else:
        subtitle = get_subtitle_path(video.name)
    lt_session.remove_torrent(handle)
    return subtitle



