#! /usr/bin/env python
import argparse
import logging
import signal

from os import kill
from os.path import abspath, dirname, join

from subprocess import PIPE, STDOUT, Popen
from time import sleep
from flask import Flask, redirect, render_template, Response
from jinja2 import FileSystemLoader

from touchandgo.helpers import get_interface, get_lock_diff, LOCKFILE, \
    set_config_dir, get_free_port
from touchandgo.history import History
from touchandgo.lock import Lock
from touchandgo.logger import log_set_up


log = logging.getLogger('touchandgo.proxy')


def serve(py_exec=None):
    log_set_up(True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default="python")
    args = parser.parse_args()

    py_exec = args.python

    app = Flask("touchandgo")
    template_path = join(dirname(__file__), "templates")
    app.jinja_loader = FileSystemLoader(template_path)

    @app.route("/favicon.ico")
    def favicon(self):
        return ""

    @app.route("/<name>")
    @app.route("/<name>/<season>/<episode>")
    def redirect_to(name, season=None, episode=None):
        log.info("Requesting %s %s %s", name, season, episode)
        interface = get_interface()
        path = abspath(__file__)
        dir_path = dirname(path)
        exec_ = join(dir_path, "__init__.py")

        port = "8890"#get_free_port()

        command = '%s %s \"%s\" ' % (py_exec, exec_, name)
        if season is not None:
            command += "%s %s " % (season, episode)
        command += "--daemon --port %s " % port
        log.debug(command)
        process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
        sleep(1)
        while get_lock_diff() < 10:
            sleep(1)
        redirect_url = "http://%s:%s" % (interface, port)
        log.info("redirecting to %s" % redirect_url)
        return redirect(redirect_url)

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
