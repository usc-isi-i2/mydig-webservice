#!/usr/bin/env bash

echo "killing backend process"
ps -ef | grep "dummy-this-is-mydig-backend" | awk '{print $2}' | xargs kill -9
echo "restart backend"
nohup python ws.py --dummy-this-is-mydig-backend &