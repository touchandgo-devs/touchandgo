import os
import logging
import signal
import socket

from daemon import DaemonContext
from datetime import datetime
from os import mkdir
from os.path import getmtime, exists, dirname, join
from shutil import copyfile

from altasetting import Settings
from netifaces import interfaces, ifaddresses
from ojota import set_data_source
from touchandgo.lock import Lock


LOCKFILE = "/tmp/touchandgo"
log = logging.getLogger('touchandgo.helpers')


def get_settings():
    settings_file = "%s/.touchandgo/settings.yaml" % os.getenv("HOME")
    default = join(dirname(__file__), "templates", "settings.yaml")

    set_config_dir()
    if not exists(settings_file):
        copyfile(default, settings_file)

    settings = Settings(settings_file, default)
    return settings


def get_free_port():
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_.bind(('localhost', 0))
    addr, port = socket_.getsockname()
    socket_.close()
    return port


def is_port_free(port):
    free = True
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        socket_.bind(('localhost', port))
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
        log.info("running daemon")
        create_process = False
        lock = Lock(LOCKFILE, os.getpid(), args.name, args.sea_ep[0],
                    args.sea_ep[1], args.port)
        if lock.is_locked():
            log.debug("lock active")
            lock_pid = lock.get_pid()
            if not lock.is_same_file(args.name, args.sea_ep[0],
                                     args.sea_ep[1]) \
                    or not is_process_running(lock_pid):
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
            create_process = True

        if create_process:
            log.debug("creating proccess")
            lock.acquire()
            callback()
            lock.release()
        else:
            log.debug("same daemon process")


def get_lock_diff():
    timediff = 0
    try:
        now = datetime.now()
        timediff = now - datetime.fromtimestamp(getmtime(LOCKFILE + ".lock"))
        timediff = timediff.total_seconds()
    except OSError:
        pass
    return timediff


def set_config_dir():
    data_folder = "%s/.touchandgo" % os.getenv("HOME")
    if not exists(data_folder):
        mkdir(data_folder)

    set_data_source(data_folder)
