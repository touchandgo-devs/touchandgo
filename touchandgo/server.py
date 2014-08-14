#! /usr/bin/env python
import argparse
import signal

from os import kill
from os.path import abspath, dirname, join

from subprocess import PIPE, STDOUT, Popen
from time import sleep
from flask import Flask, redirect, render_template, Response
from jinja2 import FileSystemLoader

from helpers import get_interface, get_lock_diff, LOCKFILE, set_config_dir
from history import History
from lock import Lock


def serve(py_exec=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default="python")
    args = parser.parse_args()

    py_exec = args.python

    app = Flask("touchandgo")
    template_path = join(dirname(__file__), "templates")
    app.jinja_loader = FileSystemLoader(template_path)

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
        process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
        sleep(1)
        while get_lock_diff() < 10:
            sleep(1)
        port = 8888
        return redirect("http://%s:%s" % (interface, port))

    @app.route("/l/<name>/<season>/<episode>")
    @app.route("/l/<name>/<season>/<episode>/")
    def list_(name, season, episode):
        url = "http://%s:5000/%s/%s" % (get_interface(), name, season)
        episode = int(episode)

        template = app.jinja_env.get_template("m3u.j2")
        ret = template.render(episodes=range(episode, episode + 10),
                              series=name, season=episode, url=url)
        return Response(response=ret, status=200,
                        mimetype="application/x-mpegurl",
                        content_type="application/x-mpegurl")

    @app.route("/kill")
    def kill_():
        lock = Lock(LOCKFILE)
        kill(lock.get_pid(), signal.SIGQUIT)
        return "OK"

    @app.route("/")
    def main():
        series = []
        keys = []
        items = History.many(sorted="-date,-season,-episode")
        for item in items:
            key = (item.name, item.season is not None)
            if key not in keys:
                series.append(item)
                keys.append(key)

        return render_template("main.html", items=series)


    set_config_dir()
    app.debug = True
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    serve()
