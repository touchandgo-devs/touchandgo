from lockfile import FileLock


class Lock(FileLock):
    def __init__(self, file_, pid=None, name=None, season=None, episode=None,
                 port=None):
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
        season = self.season if self.season is not None else ""
        episode = self.episode if self.episode is not None else ""

        file_.write(','.join((self.pid, self.name, season, episode,
                              self.port)))
        file_.close()

    def _get_file_data(self):
        try:
            file_ = open('%s.lock' % self.path, 'r')
            data = file_.read()
            parts = data.split(",")
        except IOError:
            parts = []

        return parts

    def is_same_file(self, name, season, episode):
        ret = False
        parts = self._get_file_data()
        if len(parts) > 1:
            if season is None:
                season = ''
            if episode is None:
                episode = ''
            ret = parts[1] == name and parts[2] == season and \
                parts[3] == episode
        return ret

    def get_pid(self):
        pid = self._get_file_data()[0]
        return int(pid) if pid != '' else None

