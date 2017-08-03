# mydig-webservice
FROM ubuntu:16.04

WORKDIR /app
#ADD . /app

# install required command utils
RUN apt-get update && apt-get install -y \
#RUN apt-get install -y \
    build-essential\
    python \
    python-dev \
    git \
    wget \
    jq \
    curl

# install pip
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py

# install conda
#RUN wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh && \
#    chmod +x Miniconda2-latest-Linux-x86_64.sh && \
#    ./Miniconda2-latest-Linux-x86_64.sh -p /app/miniconda -b && \
#    rm Miniconda2-latest-Linux-x86_64.sh
#ENV PATH=/app/miniconda/bin:${PATH}
#RUN conda update -y conda

# download & config mydig-webservice & dig3-resources
RUN git clone https://github.com/usc-isi-i2/mydig-webservice.git /app/mydig-webservice
RUN pip install -r /app/mydig-webservice/requirements.txt

# persistent data
VOLUME /user_data
RUN ln -s /user_data/config.py /app/mydig-webservice/ws/config.py
RUN ln -s /user_data/config_frontend.py /app/mydig-webservice/frontend/config.py

EXPOSE 9879
EXPOSE 9880

ADD run_mydig.sh /app
CMD chmod +x /app/run_mydig.sh && . /app/run_mydig.sh

# docker build -t mydig_ws .
# docker run -p 9879:9879 -p 9880:9880 -v $(pwd)/user_data:/user_data -it mydig_ws
