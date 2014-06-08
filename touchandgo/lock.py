from lockfile import FileLock

class Lock(FileLock):
    def __init__(self, file_, pid, name, season, episode, port):
        FileLock.__init__(self, file_)
        self.pid = str(pid)
        self.name = name
        self.season = season
        self.episode = episode
        self.port = port

    def acquire(self, *args, **kwargs):
        FileLock.acquire(self, *args, **kwargs)
        self._write_data()


    def _write_data(self):
        file_ = open('%s.lock' % self.path, 'w')
        file_.write(','.join((self.pid, self.name, self.season, self.episode,
                              self.port)))
        file_.close()

    def _get_file_data(self):
        file_ = open('%s.lock' % self.path, 'r')
        data = file_.read()
        parts = data.split(",")
        return parts

    def is_same_file(self, name, season, episode):
        parts = self._get_file_data()
        return parts[1] == name and parts[2] == season and parts[3] == episode

    def get_pid(self):
        return int(self._get_file_data()[0])

