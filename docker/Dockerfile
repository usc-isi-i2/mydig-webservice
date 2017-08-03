# mydig-webservice
FROM ubuntu:16.04

# all packages and environments are in /app
WORKDIR /app
#ADD . /app

# install required command utils
RUN apt-get update && apt-get install -y \
#RUN apt-get install -y \
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

# download & config mydig-webservice
RUN git clone https://github.com/usc-isi-i2/mydig-webservice.git /app/mydig-webservice
RUN pip install -r /app/mydig-webservice/requirements.txt

# download etk
RUN git clone https://github.com/usc-isi-i2/etk.git && \
    cd etk && \
    git checkout custom_spacy
# create and config conda-env (install flask for daemon process) for etk
RUN cd etk && conda-env create .
RUN /bin/bash -c "source activate etk_env && \
    python -m spacy download en && \
    pip install flask"

# persistent data
VOLUME /user_data
RUN ln -s /user_data/config.py /app/mydig-webservice/ws/config.py && \
    ln -s /user_data/config_frontend.py /app/mydig-webservice/frontend/config.py

EXPOSE 9879
EXPOSE 9880

ADD run_mydig.sh /app
CMD chmod +x /app/run_mydig.sh && /bin/bash -c "/app/run_mydig.sh"

# docker build -t mydig_ws .
# docker run -d -p 9879:9879 -p 9880:9880 -v $(pwd)/user_data:/user_data mydig_ws
