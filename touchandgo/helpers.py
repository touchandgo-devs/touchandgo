import logging
import os
import signal
import socket
from datetime import datetime
from os import mkdir
from os.path import dirname, exists, getmtime, join
from shutil import copyfile

from daemon import DaemonContext

from altasetting import Settings
from netifaces import ifaddresses, interfaces
from ojota import set_data_source
from touchandgo.lock import Lock
from touchandgo.settings import (BIND_ADDRESS, LOCK_FILE, SETTINGS_FILE,
                                 SETTINGS_FOLDER)


log = logging.getLogger('touchandgo.helpers')


def get_settings():
    home = os.getenv("HOME")
    settings_file = join(home, SETTINGS_FOLDER, SETTINGS_FILE)
    default = join(dirname(__file__), "templates", SETTINGS_FILE)

    set_config_dir()
    if not exists(settings_file):
        copyfile(default, settings_file)

    settings = Settings(settings_file, default)
    return settings


def get_free_port():
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_.bind((BIND_ADDRESS, 0))
    addr, port = socket_.getsockname()
    socket_.close()
    return port


def is_port_free(port):
    free = True
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        socket_.bind((BIND_ADDRESS, port))
    except socket.error:
        free = False
    socket_.close()

    return free


def get_interface():
    for ifaceName in interfaces():
        addresses = ifaddresses(ifaceName)
        for address in addresses.values():
            for item in address:
                if item.get('netmask') is not None and \
                        not item['addr'].startswith("127") and \
                        not item['addr'].startswith(":") and \
                        len(item['addr']) < 17:
                    return item['addr']


def is_process_running(process_id):
    try:
        os.kill(process_id, 0)
        return True
    except OSError:
        return False


def daemonize(args, callback):
    with DaemonContext():
        from touchandgo.logger import log_set_up
        log_set_up(True)
        log = logging.getLogger('touchandgo.daemon')
        try:
            log.info("running daemon")
            create_process = False
            pid = os.getpid()
            log.debug("%s, %s, %s", LOCK_FILE, pid, args)
            lock = Lock(LOCK_FILE, pid, args.name, args.season_number,
                        args.episode_number, args.port)
            if lock.is_locked():
                log.debug("lock active")
                lock_pid = lock.get_pid()
                is_same = lock.is_same_file(args.name, args.season_number,
                                            args.episode_number)
                if (not is_same or not is_process_running(lock_pid)):
                    try:
                        log.debug("killing process %s" % lock_pid)
                        os.kill(lock_pid, signal.SIGQUIT)
                    except OSError:
                        pass
                    except TypeError:
                        pass
                    lock.break_lock()
                    create_process = True
            else:
                log.debug("Will create process")
                create_process = True

            if create_process:
                log.debug("creating proccess")
                lock.acquire()
                callback()
                lock.release()
            else:
                log.debug("same daemon process")
        except Exception as e:
            log.error(e)


def get_lock_diff():
    timediff = 0
    try:
        now = datetime.now()
        timediff = now - datetime.fromtimestamp(getmtime(LOCK_FILE))
        timediff = timediff.total_seconds()
    except OSError:
        pass
    return timediff


def set_config_dir():
    home = os.getenv("HOME")
    data_folder = join(home, SETTINGS_FOLDER)
    if not exists(data_folder):
        mkdir(data_folder)

    set_data_source(data_folder)
