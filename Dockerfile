# mydig-webservice
FROM ubuntu:16.04

# all packages and environments are in /app
WORKDIR /app

# install required command utils
RUN apt-get update && apt-get install -y \
    build-essential \
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
RUN wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh && \
    chmod +x Miniconda2-latest-Linux-x86_64.sh && \
    ./Miniconda2-latest-Linux-x86_64.sh -p /app/miniconda -b && \
    rm Miniconda2-latest-Linux-x86_64.sh
ENV PATH=/app/miniconda/bin:${PATH}
RUN conda update -y conda

# download etk
RUN git clone https://github.com/usc-isi-i2/etk.git && \
    cd etk && \
    git checkout development
# create and config conda-env (install flask for daemon process) for etk
RUN cd etk && conda-env create .
RUN /bin/bash -c "source activate etk_env && \
    python -m spacy download en && \
    pip install flask"

# install dependencies of mydig
ADD requirements.txt /app
RUN pip install -r requirements.txt

# persistent data
VOLUME /shared_data

EXPOSE 9879
EXPOSE 9880

# mydig-webservice
RUN mkdir /app/mydig-webservice
ADD . /app/mydig-webservice
CMD chmod +x /app/mydig-webservice/docker_run_mydig.sh && \
    /bin/bash -c "/app/mydig-webservice/docker_run_mydig.sh"

# docker build -t mydig_ws .
# docker run -d -p 9879:9879 -p 9880:9880 \
# -v $(pwd)/ws/config_docker.py:/app/mydig-webservice/ws/config.py \
# -v $(pwd)/../mydig-projects:/shared_data/projects \
# -v $(pwd)/../dig3-resources:/shared_data/dig3-resources \
# mydig_ws
