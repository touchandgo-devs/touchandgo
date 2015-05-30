from touchandgo.helpers import set_config_dir


def with_config_dir(func):
    def _inner(*args, **kwargs):
        set_config_dir()
        return func(*args, **kwargs)

    return _inner

