import argparse

from subprocess import PIPE, STDOUT, Popen
from time import sleep
from flask import Flask, redirect

from helpers import get_interface

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
        command = "%s touchandgo.py \"%s\" " % (py_exec, name)
        if season is not None:
            command += "%s %s " % (season, episode)
        command += "--daemon"
        print command
        process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
        sleep(10)
        port = 8888
        return redirect("http://%s:%s" % (interface, port))

    app.debug = True
    app.run(host="0.0.0.0")

if __name__ == '__main__':
    serve()
