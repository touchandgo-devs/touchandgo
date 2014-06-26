import argparse

from os.path import abspath, dirname, join, getmtime

from subprocess import PIPE, STDOUT, Popen
from time import sleep, ctime
from datetime import datetime
from flask import Flask, redirect

from helpers import get_interface, LOCKFILE


def serve(py_exec=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default="python")
    args = parser.parse_args()

    py_exec = args.python

    app = Flask("touchandgo")

    @app.route("/<name>")
    @app.route("/<name>/<season>/<episode>")
    def redirect_to(name, season=None, episode=None):
        interface = get_interface()
        path = abspath(__file__)
        dir_path = dirname(path)
        exec_ = join(dir_path, "touchandgo.py")
        command = '%s %s \"%s\" ' % (py_exec, exec_, name)
        if season is not None:
            command += "%s %s " % (season, episode)
        command += "--daemon"
        print "running", command
        process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
        now = datetime.now()
        timediff = now - datetime.fromtimestamp(getmtime(LOCKFILE + ".lock"))
        while timediff.total_seconds() < 10:
            sleep(1)
            now = datetime.now()
            timediff = now - datetime.fromtimestamp(getmtime(LOCKFILE + ".lock"))
            print "waiting"
        port = 8888
        return redirect("http://%s:%s" % (interface, port))

    app.debug = True
    app.run(host="0.0.0.0")

if __name__ == '__main__':
    serve()
