import logging
from touchandgo.helpers import have_moov


log = logging.getLogger('touchandgo.strategy')


class DefaultStrategy(object):
    def __init__(self, manager):
        self.manager = manager
        self.piece_st = 4
        self.last_piece_st = 2
        self.holding_stream = True
        self.handle = manager.handle
        self.chunks_strat = 10
        self.moov_downloaded = False
        self.download_lasts = False

    def initial(self):
        self.handle.set_sequential_download(True)
        status = self.handle.status()

        for i in range(self.piece_st):
            self.handle.piece_priority(i, 7)
            self.handle.set_piece_deadline(i, 3000)

        self.chunks_strat = len(status.pieces) / 30

    def block_requested(self, block_requested):
        #log.debug("block requested %s" % block_requested)
        if not self.holding_stream:
            self.move_strategy(block_requested)

    def master(self):
        status = self.handle.status()
        pieces = status.pieces
        last_piece = len(status.pieces)
        first_n = pieces[:self.piece_st]
        if self.download_lasts:
            last_n = pieces[-self.last_piece_st:]
        else:
            last_n = []

        if all(first_n) and all(last_n):
            log.debug("first_n downloaded")
            if not self.moov_downloaded:
                video_file = self.manager.get_video_path()
                self.moov_downloaded = have_moov(video_file)
                log.debug("Moov Downloaded = %s", self.moov_downloaded)

            if self.moov_downloaded:
                self.handle.set_sequential_download(False)
                if not self.holding_stream:
                    self.piece_st += self.chunks_strat
                else:
                    self.holding_stream = False
                    self.manager.stream()
                self.move_strategy(self.piece_st)
            else:
                log.debug("video doesn't have moov yet. Extending first_n")
                for i in range(last_piece - self.piece_st, last_piece):
                    self.handle.piece_priority(i, 7)
                    self.handle.set_piece_deadline(i, 3000)

                for i in range(self.piece_st):
                    self.handle.piece_priority(i, 7)
                    self.handle.set_piece_deadline(i, 3000)

                self.piece_st *= 2
                self.last_piece_st *= 2
                log.debug("piece_st = %s last_piece_st %s",
                          self.piece_st, self.last_piece_st)
                self.download_lasts = True

    def reset_priorities(self):
        for i in range(len(self.handle.status().pieces)):
            self.handle.piece_priority(i, 1)

    def move_strategy(self, first_block):
        log.debug("moving strategy %s" % first_block)
        self.reset_priorities()
        self.piece_st = first_block

        #self.handle.set_sequential_download(True)
        status = self.handle.status()
        last_piece = len(status.pieces) - 1

        last_chunks = first_block + self.chunks_strat
        if last_chunks > last_piece:
            last_chunks = last_piece

        for i in range(first_block, last_chunks):
            self.handle.piece_priority(i, 7)
            self.handle.set_piece_deadline(i, 10000)

        last_chunks = first_block + self.chunks_strat * 2
        if last_chunks > last_piece:
            last_chunks = last_piece
        for i in range(first_block+self.chunks_strat, last_chunks):
            self.handle.piece_priority(i, 3)
            #self.handle.set_piece_deadline(i, 20000)
