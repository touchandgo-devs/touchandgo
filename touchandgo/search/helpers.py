from gzip import GzipFile
from BeautifulSoup import BeautifulSoup
from urllib import urlopen
from StringIO import StringIO


def kat_html2magnet(url):
    site = GzipFile(fileobj=StringIO(urlopen(url).read())).read()
    soup = BeautifulSoup(site)
    magnet = soup.find('a', title='Magnet link')['href']
    return magnet
