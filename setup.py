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
    install_requires=[
        'altasetting==0.1.1',
        'blessings==1.6',
        'colorama==0.3.2',
        'flask==0.10.1',
        'guessit==2.0.5',
        'KickassAPI==1.0.4',
        'netifaces==0.10.4',
        'ojota==2.0.1',
        'pbr==1.10.0',
        'PyChromecast==0.7.3',
        'pyQuery==1.2.13',
        'python-daemon==1.6.1',
        'pyyaml==15.8.2',
        'qtfaststart==1.8',
        'requests==2.3.0',
        'simplejson==3.6.2',
        'subliminal==2.0.3',
        'TorrentMediaSearcher==1.0.3',
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
