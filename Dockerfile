FROM ubuntu:latest
MAINTAINER Felipe Lerena <felipelerena@gmail.com>
RUN apt-get update && apt-get install python-pip libtorrent-rasterbar8 python-libtorrent libxml2-dev libxslt1-dev python-lxml python-dev python-yaml -y
COPY . /app
WORKDIR /app
RUN python /app/setup.py install
