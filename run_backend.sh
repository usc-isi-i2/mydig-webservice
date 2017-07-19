#!/bin/sh
cd /github/mydig-webservice/ws
nohup python ws.py --dummy-this-is-mydig-backend > /dev/null 2>&1 &

