#! /usr/bin/env python2
import argparse
import logging
import requests
import signal

from os import kill
from os.path import abspath, dirname, join

from subprocess import PIPE, STDOUT, Popen
from time import sleep
from flask import Flask, redirect, render_template, Response, request
from jinja2 import FileSystemLoader

from touchandgo.helpers import get_interface, LOCKFILE, get_free_port, \
    is_process_running
from touchandgo.history import History
from touchandgo.decorators import with_config_dir
from touchandgo.logger import log_set_up
from touchandgo.settings import DEBUG
from touchandgo.lock import Lock


log = logging.getLogger('touchandgo.proxy')


@with_config_dir
def serve(py_exec=None):
    log_set_up(DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default="python2")
    args = parser.parse_args()

    py_exec = args.python

    app = Flask("touchandgo")
    template_path = join(dirname(__file__), "templates")
    app.jinja_loader = FileSystemLoader(template_path)

    def get_torrent(name, season=None, episode=None):
        interface = get_interface()
        path = abspath(__file__)
        dir_path = dirname(path)
        exec_ = join(dir_path, "__init__.py")
        command = '%s %s \"%s\" ' % (py_exec, exec_, name)
        if season is not None:
            command += "%s %s " % (season, episode)
        lock = Lock(LOCKFILE)
        if lock.is_same_file(name, season, episode) and \
                is_process_running(lock.get_pid()):
            data = lock._get_file_data()
            port = data[4]
        else:
            port = get_free_port()
            command += "--daemon --port %s " % port
            log.debug(command)
            process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
            sleep(1)

        redirect_url = "http://%s:%s" % (interface, port)
        serving = False
        while not serving:
            try:
                req = requests.get("%s/status" % redirect_url)
                serving = True
            except requests.ConnectionError, e:
                sleep(1)
        log.info("redirecting to %s" % redirect_url)
        return redirect(redirect_url)

    @app.route("/favicon.ico")
    def favicon():
        return ""

    @app.route("/magnet")
    def magnet():
        # Maybe someone wanted to search the movie "magnet", who knows
        return get_torrent(request.args.get('m', 'magnet'))

    @app.route("/<name>")
    @app.route("/<name>/<season>/<episode>")
    def redirect_to(name, season=None, episode=None):
        log.info("Requesting %s %s %s", name, season, episode)
        return get_torrent(name, season, episode)

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
        try:
            kill(lock.get_pid(), signal.SIGQUIT)
        except Exception, e:
            pass
        return "OK"

    @app.route("/")
    def main():
        series = []
        keys = []
        items = History.many(sorted="-date,-season,-episode")

        # Filter duplicate entries in the history list
        for item in items:
            key = (item.name, item.season is not None)
            if key not in keys:
                series.append(item)
                keys.append(key)

        return render_template("main.html", items=series, magnet=request.args.get('m', ''))

    app.debug = True
    kill_()
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    serve()
