from pyquery import PyQuery as pq
from requests import get


class SearchSky:
    def __init__(self, search_string):
        self.search_string = search_string
        self.domain = "https://www.skytorrents.in"
        self.search_url = "{}/search/all/ed/1/?q={}"
        self.results = []

    def list(self):
        url = self.search_url.format(self.domain,
                                     self.search_string)
        req = get(url)
        page = pq(req.content)
        table = page(".table tbody")

        for elem in table('tr'):
            result = {}

            children = elem.getchildren()
            td = pq(children[0])
            print(td)

            result['url'] = pq(td("a")[2]).attr("href")
            result['name'] = pq(td("a")[0]).text()

            result['size'] = pq(children[1]).text()
            result['seeds'] = pq(children[4]).text()
            result['leechs'] = pq(children[5]).text()

            self.results.append(result)

        return self.results

    def get_magnet(self, index):
        result = self.results[index]
        extra_tracker = "&tr=http%3A%2F%2Ftracker.nwps.ws%3A6969%2Fannounce"

        result["magnet"] = result["url"] + extra_tracker

        return result
