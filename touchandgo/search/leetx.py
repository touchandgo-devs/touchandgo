from pyquery import PyQuery as pq
from requests import get


class Search1337x:
    def __init__(self, search_string):
        self.search_string = search_string
        self.domain = "http://1337x.to"
        self.search_url = "{}/search/{}/1/"
        self.results = []

    def list(self):
        url = self.search_url.format(self.domain,
                                     self.search_string)
        req = get(url)
        page = pq(req.content)
        table = page(".table-list tbody")

        for elem in table('tr'):
            result = {}
            tr = pq(elem)
            result['name'] = tr(".coll-1").text()
            result['seeds'] = tr(".coll-2").text()
            result['leechs'] = tr(".coll-3").text()
            result['size'] = tr(".coll-4").text()
            result['url'] = pq(tr(".coll-1 a")[1]).attr("href")

            self.results.append(result)

        return self.results

    def get_magnet(self, index):
        result = self.results[index]
        torrent_page = "".join([self.domain, result['url']])
        req = get(torrent_page)
        page = pq(req.content)
        magnet = page(".btn-magnet").attr("href")
        extra_tracker = "&tr=http%3A%2F%2Ftracker.nwps.ws%3A6969%2Fannounce"

        result["magnet"] = magnet + extra_tracker

        return result
