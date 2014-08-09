from ojota import Ojota


class History(Ojota):
    required_fields = ["date", "name", "season", "episode"]
    pk_field = "date"
    plural_name = "history"

    @property
    def next(self):
        return int(self.episode) + 1
