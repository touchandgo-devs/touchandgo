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
    version='0.12.1',
    author='Felipe Lerena, Nicolás Demarchi',
    description='A python app and library to watch series magically',
    author_email='felipelerena@gmail.com - mail@gilgamezh.me',
    packages=['touchandgo'],
    scripts=[],
    url='https://github.com/touchandgo-devs/touchandgo/',
    license='LICENSE.txt',
    long_description=open('README.rst').read(),
    install_requires=['TorrentMediaSearcher',
                      'subliminal',
                      'netifaces',
                      'flask',
                      'simplejson',
                      'python-daemon',
                      'ojota',
                      'pyaml',
                      'colorama',
                      'requests',
                      'qtfaststart',
                      'KickassAPI',
                      'pyQuery',
                      'altasetting',
                      'blessings'
                      ],
    entry_points={
        'console_scripts': ['touchandgo = touchandgo.__init__:main',
                            'tsproxy = touchandgo.tsproxy.__init__:serve']
    },
    package_data={
        'touchandgo': ['templates/*'],
    },
)
