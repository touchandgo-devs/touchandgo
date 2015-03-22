#! /usr/bin/env python2

# Get torrents from http://getstrike.net

import requests


class StrikeAPI():
    "Search torrents using http://getstrike.net/api/"
    def __init__(self, search_string):
        self.url = "http://getstrike.net/api/torrents"
        self.search_string = search_string
        self.headers = {'User-Agent': 'TouchAndGo (+https://github.com/touchandgo-devs/touchandgo)'}

    def search(self):
        search_url = '%s/search/' % (self.url)
        payload = {'q': self.search_string}
        response = requests.get(search_url, params=payload,
                                headers=self.headers)
        torrents = response.json()
        return torrents

    def get_first_torrent_magnet(self):
        torrents = self.search()
        first_torrent_hash = torrents[1][0]['torrent_hash']
        info_url = '%s/info/' % (self.url)
        payload = {'hashes': first_torrent_hash}
        response = requests.get(info_url, params=payload, headers=self.headers)
        magnet = response.json()[1][0]['magnet_uri']
        return magnet








