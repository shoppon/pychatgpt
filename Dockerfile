FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN sed -i "s/archive.ubuntu.com/mirrors.aliyun.com/g" /etc/apt/sources.list /etc/apt/sources.list && \
    rm -Rf /var/lib/apt/lists/* && \
    apt-get update

RUN apt-get -y install wget python3 python3-pip xvfb

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub > /usr/share/keyrings/chrome.pub && \
    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/chrome.pub] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list && \
    apt update -y && \
    apt install -y google-chrome-stable

# for quicker build
COPY requirements.txt /opt/pychatgpt/requirements.txt
RUN pip install -r /opt/pychatgpt/requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

COPY . /opt/pychatgpt/
RUN cd /opt/pychatgpt/ && python3 setup.py install --old-and-unmanageable

CMD ["/bin/bash"]
