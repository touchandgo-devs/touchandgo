.. Touchandgo documentation master file, created by
   sphinx-quickstart on Tue Oct 28 02:08:26 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Touchandgo's documentation!
======================================

Touchandgo is a CLI application and python library to download and stream
torrents


Using touchandgo
----------------

::

  touchandgo [movie name]
  touchandgo [series name] [season] [episode]
 
  E.g.:  touchandgo Crisis 1 5
         touchandgo "true blood" 7 10
         touchandgo "true blood" 7 10 --sub spa
         touchandgo "never ending story"

Parameters
++++++++++

::

    positional arguments:
    name                  The name of the series or movie
    season_number         Season number
    episode_number        Episode number

    optional arguments:
    -h, --help            show this help message and exit
    --sub [SUB]           Subtitle language
    --serve               Do not run VLC
    --quality [QUALITY]   quality of the video [normal|hd|fullhd]
    --daemon              Daemonize the process
    --port PORT, -p PORT  The port where the stream will be served
    --verbose             Show _all_ the logs
    --search SEARCH       search lib to use (only option right now is 'kat' for
                          kickass torrents)
    --nocache             Search for the torrent again



How to run streaming proxy
--------------------------

In the command line

::

  tsproxy 


In your browser open http://<server address>:5000 to use de web UI

In your video player open http://<server address>:5000/crisis/1/5 Equivalent to
"touchandgo Crisis 1 5" but directly in the player :D


just enjoy it.

Requierements
-------------

Ubuntu
++++++
    * python-libtorrent
    * python-dev

  ::

    sudo apt-get install python-libtorrent python-dev

How to install
--------------

::

  pip install touchandgo


Debugging
---------

If you run Touchandgo in debug mode (with --verbose), 
You will see this (see the screenshot)that we call"defrag". 
Defrag shows the current pieces status.

.. figure:: screenshots/touchandgo.png
    :align: center

    *Example of the command line output*

* The number shows the piece priority. 1 is the lowest and 7 the highest.
* v means that the piece is downloading.
* # means that the piece is downloaded.
* > means that the piece was served by http.

Contribute
----------
https://github.com/touchandgo-devs/touchandgo/


Join the discussion
-------------------
touchandgo-devs@googlegroups.com or https://groups.google.com/forum/#!forum/touchandgo-devs

Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

