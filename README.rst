Touchandgo
==========
A python app and library to watch series magically

How to install
--------------

::

  pip install touchandgo


How to use
----------

::

  touchandgo [series name] [season] [episode]
 
  E.g.:  touchandgo Crisis 1 5


How to run streaming proxy
_______________


In the computer

::

  tsproxy 


In your video player open http://<server address>:5000/crisis/1/5

just enjoy it.


Requirements
------------
* TorrentMediaSearcher
* subliminal
* netifaces
* flask
* simplejson
* python-libtorrent (via apt)
* peerflix (via npm)
* VLC
