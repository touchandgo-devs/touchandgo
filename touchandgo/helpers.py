import os
import re
import signal
import socket

from daemon import DaemonContext
from lock import Lock

from subprocess import PIPE, STDOUT, Popen
from netifaces import interfaces, ifaddresses


LOCKFILE = "/tmp/touchandgo"


def get_free_port():
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_.bind(('localhost', 0))
    addr, port = socket_.getsockname()
    socket_.close()
    return port


def get_interface():
    for ifaceName in interfaces():
        addresses = ifaddresses(ifaceName)
        for address in addresses.values():
            for item in address:
                if item.get('netmask') is not None and \
                        not item['addr'].startswith("127") and \
                        not item['addr'].startswith(":"):
                    return item['addr']


def is_process_running(process_id):
    try:
        os.kill(process_id, 0)
        return True
    except OSError:
        return False


def execute(command):
    process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
    print("Running peerflix")
    while True:
        nextline = process.stdout.readline()
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                          nextline)
        if len(urls):
            print("streaming url: %s" % urls[0])
            break
        if nextline == '' and process.poll() is not None:
            break

    output = process.communicate()[0]
    exitCode = process.returncode
    #print output, exitCode


def daemonize(args, callback):
    with DaemonContext():
        create_process = False
        lock = Lock(LOCKFILE, os.getpid(), args.name, args.sea_ep[0],
                    args.sea_ep[1], args.port)
        if lock.is_locked():
            lock_pid = lock.get_pid()
            if not lock.is_same_file(args.name, args.sea_ep[0],
                                     args.sea_ep[1]) \
                    or not is_process_running(lock_pid):
                try:
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
            lock.acquire()
            callback(args.name, season=args.sea_ep[0], episode=args.sea_ep[1],
                     serve=True, port=args.port)
            lock.release()
