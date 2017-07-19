# mydig-webservice
FROM debian:jessie

RUN apt-get update && apt-get install -y \
    python \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py

EXPOSE 9876

RUN mkdir -p /github
RUN git clone https://github.com/usc-isi-i2/mydig-webservice.git /github/mydig-webservice

RUN git clone https://github.com/usc-isi-i2/mydig-projects-public.git /github/mydig-projects
RUN git clone https://github.com/usc-isi-i2/mydig-projects-landmark-public.git /github/mydig-projects-landmark
#RUN mkdir /mydig-webservice/ws

RUN mv /github/mydig-webservice/ws/sample_config.py /github/mydig-webservice/ws/config.py
#COPY run_backend.sh /mydig-webservice
#COPY ws/* /mydig-webservice/ws/

#RUN mkdir -p /etc/sandpaper/config
#COPY config/sandpaper.json /etc/sandpaper/config
#VOLUME /etc/sandpaper/config
#VOLUME /mydig-webservice

WORKDIR /github/mydig-webservice

RUN pip install -r requirements.txt

# WORKDIR /github/mydig-webservice/ws
# RUN PATH="/github/mydig-webservice/ws:$PATH"

RUN ["chmod", "+x", "/github/mydig-webservice/ws/run_backend.sh"]
CMD ./run_backend.sh
