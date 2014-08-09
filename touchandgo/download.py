from time import sleep

from libtorrent import add_magnet_uri, session


def download(magnet):
    lt_session = session()
    params = {"save_path": TMP_DIR,
              "allocation": "compact"}
    handle = add_magnet_uri(lt_session, magnet, params)

    while not handle.has_metadata():
        sleep(.1)
    info = handle.get_torrent_info()
    files = info.files()
    lt_session.listen_on(6881, 6891)
    lt_session.start_dht()

    biggest_file = ("", 0)

    for file_ in files:
        if file_.size > biggest_file[1]:
            biggest_file = [file_.path, file_.size]

    handle.set_sequential_download(True)
    status = handle.status()
    chunks_strat = len(status.pieces) / 25
    print "chunks_strat", chunks_strat
    piece_strat = 5
    estrat_orig = True

    for i in range(piece_strat):
        handle.piece_priority(i, 7)
        handle.set_piece_deadline(i, 10000)


    while not handle.is_seed():
        status = handle.status()
        pieces = status.pieces
        primera = pieces[:piece_strat]

        if all(primera):
            handle.set_sequential_download(False)
            pieces_strat = pieces[piece_strat:piece_strat + chunks_strat]
            if estrat_orig or all(pieces_strat):
                piece_strat += chunks_strat
                for i in range(piece_strat, piece_strat + chunks_strat):
                    handle.piece_priority(i, 7)
                    handle.set_piece_deadline(i, 10000)
                estrat_orig = False


        numerales = ""
        for i, piece in enumerate(pieces):
            numeral = "#" if piece else " "
            numeral += str(handle.piece_priority(i))
            numerales += numeral
        print numerales

        state_str = ['queued', 'checking', 'downloading metadata', \
                     'downloading', 'finished', 'seeding', 'allocating']
        print '%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
                (status.progress * 100, status.download_rate / 1000, status.upload_rate / 1000, \
                 status.num_peers, state_str[status.state])

        sleep(1)


TMP_DIR = "/tmp"

magnet = "magnet:?xt=urn:btih:d9bdf203693c508cbff515602ea4898ae2ffa4a6&dn=Suits+S04E08+HDTV+x264-KILLERS%5Bettv%5D&tr=udp%3A//tracker.openbittorrent.com%3A80&tr=udp%3A//tracker.publicbt.com%3A80&tr=udp%3A//tracker.istole.it%3A6969&tr=udp%3A//open.demonii.com%3A1337"
download(magnet)
