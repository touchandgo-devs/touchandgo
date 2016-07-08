#!/usr/bin/env python2
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='Touchandgo',
    version='0.13.0',
    author='Felipe Lerena, Nicolás Demarchi',
    description='A python app and library to watch series magically',
    author_email='felipelerena@gmail.com - mail@gilgamezh.me',
    packages=['touchandgo'],
    scripts=[],
    url='https://github.com/touchandgo-devs/touchandgo/',
    license='LICENSE.txt',
    long_description=open('README.rst').read(),
    install_requires=['TorrentMediaSearcher==1.0.3',
                      'subliminal==0.7.4',
                      'netifaces==0.10.4',
                      'flask==0.10.1',
                      'simplejson==3.6.2',
                      'python-daemon==1.6.1',
                      'ojota==2.0.1',
                      'pyaml',
                      'colorama==0.3.2',
                      'requests==2.3.0',
                      'qtfaststart==1.8',
                      'KickassAPI',
                      'pyQuery',
                      'altasetting',
                      'blessings',
                      'guessit==0.6.2',
                      'pbr',
                      'PyChromecast==0.6.13',
                      ],
    entry_points={
        'console_scripts': ['touchandgo = touchandgo.main:main',
                            'tsproxy = touchandgo.tsproxy.__init__:serve']
    },
    package_data={
        'touchandgo': ['templates/*',
                       'download/*.py',
                       'search/*.py',
                       'tsproxy/*.py'],
    },
)
