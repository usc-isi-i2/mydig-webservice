# mydig-webservice
FROM debian:jessie

RUN apt-get update && apt-get install -y \
    python \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py

EXPOSE 9880

RUN mkdir -p /github
RUN git clone https://github.com/usc-isi-i2/mydig-webservice.git /github/mydig-webservice
#RUN mkdir /mydig-webservice/ws

#COPY requirements.txt /mydig-webservice
#COPY run_backend.sh /mydig-webservice
#COPY ws/* /mydig-webservice/ws/

#RUN mkdir -p /etc/sandpaper/config
#COPY config/sandpaper.json /etc/sandpaper/config
#VOLUME /etc/sandpaper/config
#VOLUME /mydig-webservice

WORKDIR /github/mydig-webservice

RUN pip install -r requirements.txt

CMD ["run_backend.sh"]
