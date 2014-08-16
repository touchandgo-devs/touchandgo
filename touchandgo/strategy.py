class DefaultStrategy(object):
    def __init__(self, manager):
        self.manager = manager
        self.piece_st = 4
        self.holding_stream = True
        self.handle = manager.handle

    def initial(self):
        self.handle.set_sequential_download(True)
        status = self.handle.status()

        for i in range(self.piece_st):
            self.handle.piece_priority(i, 7)
            self.handle.set_piece_deadline(i, 1000)

        last_piece = len(status.pieces) - 1
        for i in range(last_piece-4, last_piece+1):
            self.handle.piece_priority(i, 7)
            self.handle.set_piece_deadline(i, 1000)

        return len(status.pieces) / 25

    def master(self, chunks_strat):
        status = self.handle.status()
        pieces = status.pieces
        first_n = pieces[:self.piece_st] + pieces[-5:]

        if all(first_n):
            #self.handle.set_sequential_download(False)
            pieces_strat = pieces[self.piece_st:self.piece_st + chunks_strat]
            if self.holding_stream or all(pieces_strat):
                if not self.holding_stream:
                    self.piece_st += chunks_strat
                else:
                    self.manager.stream()

                for i in range(self.piece_st, self.piece_st + chunks_strat):
                    self.handle.piece_priority(i, 7)
                    self.handle.set_piece_deadline(i, 10000)

                for i in range(self.piece_st+chunks_strat,
                               self.piece_st+chunks_strat*2):
                    self.handle.piece_priority(i, 5)
                    self.handle.set_piece_deadline(i, 20000)
                self.holding_stream = False

