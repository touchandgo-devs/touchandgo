from time import sleep
from babelfish import Language
from subliminal import download_best_subtitles, scan_videos
from libtorrent import add_magnet_uri, session

def get_subtitle():
    print("Explorando torrent")
    lt_session = session()
    params = {"save_path": "/tmp"}
    handle = add_magnet_uri(lt_session, magnet, params)
    while (not handle.has_metadata()):
        sleep(.1)
    info = handle.get_torrent_info()
    files = info.files()

    biggest_file = ("", 0)

    for file_ in files:
        if file_.size > biggest_file[1]:
            biggest_file = [file_.path, file_.size]

    videos = scan_videos(['/home/felipe/Downloads'], subtitles=True, embedded_subtitles=True)#, age=timedelta(weeks=1))
    print videos
    download_best_subtitles(biggest_file[0], {Language('spa')})#, age=timedelta(week=1))

    print("Bajando el subtitulo")

