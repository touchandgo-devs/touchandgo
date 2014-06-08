Touchandgo
==========
A python app and library to watch series magically

How to use
----------

::

  python touchandgo.py [series name] [season] [episode]
 
  E.g.:  python touchandgo.py Crisis 1 5


streaming proxy:


in the computer

::

  python server.py


in your video player open http://<server address>:5000/crisis/1/5

just enjoy it.



Requirements
------------
* TorrentMediaSearcher
* netifaces
* flask
* python-libtorrent (via apt)
* peerflix (via npm)
* VLC
