from ojota import Ojota


class History(Ojota):
    required_fields = ["date", "name", "season", "episode"]
    pk_field = "date"
    plural_name = "history"

    @property
    def next(self):
        if self.episode is not None:
            return int(self.episode) + 1
