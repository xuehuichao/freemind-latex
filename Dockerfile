FROM ubuntu:14.04
MAINTAINER Huichao Xue

RUN apt-get update && apt-get install -y texlive-full python python-pip
RUN apt-get install -y python-dev
ADD setup.py requirements.txt /freemindlatex/
ADD src/freemindlatex/* /freemindlatex/src/freemindlatex/
WORKDIR /freemindlatex
RUN pip install .
EXPOSE 8117
CMD freemindlatex --port 8117 server
