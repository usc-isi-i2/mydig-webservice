#!/usr/bin/env bash

cd /app/mydig-webservice/ws
chmod +x backend.sh
./backend.sh

cd /app/mydig-webservice/frontend
chmod +x frontend.sh
./frontend.sh

# open bash and wait
bash


