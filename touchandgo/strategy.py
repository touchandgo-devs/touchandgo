class DefaultStrategy(object):
    def __init__(self, manager):
        self.manager = manager
        self.piece_st = 4
        self.holding_stream = True
        self.handle = manager.handle
        self.chunks_strat = 10

    def initial(self):
        self.handle.set_sequential_download(True)
        status = self.handle.status()

        #for i in range(self.piece_st):
        #    self.handle.piece_priority(i, 7)
        #    self.handle.set_piece_deadline(i, 3000)

        last_piece = len(status.pieces) - 1
        for i in range(last_piece-4, last_piece+1):
            self.handle.piece_priority(i, 7)
            self.handle.set_piece_deadline(i, 1000)

        self.chunks_strat = len(status.pieces) / 30

    def block_requested(self, block_requested):
        if not self.holding_stream:
            self.move_strategy(block_requested)

    def master(self):
        status = self.handle.status()
        pieces = status.pieces
        first_n = pieces[:self.piece_st] + pieces[-5:]

        if all(first_n):
            self.handle.set_sequential_download(False)
            pieces_strat = pieces[self.piece_st:self.piece_st + self.chunks_strat]
            if self.holding_stream or all(pieces_strat):
                if not self.holding_stream:
                    self.piece_st += self.chunks_strat
                else:
                    self.holding_stream = False
                    self.manager.stream()
                self.move_strategy(self.piece_st)

    def reset_priorities(self):
        for i in range(len(self.handle.status().pieces)):
            self.handle.piece_priority(i, 1)

    def move_strategy(self, first_block):
        self.reset_priorities()
        self.piece_st = first_block
        for i in range(first_block, first_block + self.chunks_strat):
            self.handle.piece_priority(i, 7)
            self.handle.set_piece_deadline(i, 10000)

        for i in range(first_block+self.chunks_strat,
                       first_block+self.chunks_strat*2):
            self.handle.piece_priority(i, 3)
            #self.handle.set_piece_deadline(i, 20000)
