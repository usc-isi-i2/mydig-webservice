#!/bin/bash

export PS1="\u:\W\$ "

# daemon
#source activate etk_env
cd /app/mydig-webservice/daemon
chmod +x daemon.sh
./daemon.sh
#source deactivate

# backend
cd /app/mydig-webservice/ws
chmod +x backend.sh
./backend.sh

# frontend
cd /app/mydig-webservice/frontend
chmod +x frontend.sh
./frontend.sh

# spacy_ui
cd /app/spacy-ui
nohup /usr/bin/serve -s build -p 9881 &

# open bash and wait
#cd /app
#/bin/bash
while true; do sleep 1000; done


