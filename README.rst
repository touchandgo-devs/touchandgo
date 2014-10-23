Touchandgo
==========
A python app and library to watch series and movies magically

How to install
--------------

::

  sudo apt-get install python-libtorrent (or the name of the package on your
  linux distro)
  pip install touchandgo
  (pip needs python-dev package to compile some libraries. If you don't 
  have installed run "sudo sudo apt-get install python-dev")


How to use
----------

::

  touchandgo [series name] [season] [episode]
 
  E.g.:  touchandgo Crisis 1 5
         touchandgo "true blood" 7 10
         touchandgo "true blood" 7 10 --sub spa
         touchandgo "never ending story"


How to run streaming proxy
--------------------------


In the computer

::

  tsproxy 


In your video player open http://<server address>:5000/crisis/1/5

just enjoy it.

