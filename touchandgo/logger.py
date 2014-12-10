import logging
import sys

from logging.handlers import RotatingFileHandler
from os import mkdir
from os.path import exists

from touchandgo.helpers import get_settings
from touchandgo.settings import DEBUG


def log_set_up(verbose=False):
    settings = get_settings()
    if not exists(settings.save_path):
        mkdir(settings.save_path)

    logfile = "%s/touchandgo.log" % (settings.save_path)
    handler = RotatingFileHandler(logfile, maxBytes=1e6, backupCount=10)
    formatter = logging.Formatter("%(asctime)s  %(name)-22s  "
                                  "%(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    if DEBUG or verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    add_stdout_handler(logger, formatter)


def add_stdout_handler(logger, formatter):
    try:
        from rainbow_logging_handler import RainbowLoggingHandler
        handler = RainbowLoggingHandler(sys.stderr, color_funcName=(
            'black', 'black', True))
    except ImportError:
        handler = logging.StreamHandler()
        pass

    handler.setFormatter(formatter)
    logger.addHandler(handler)
