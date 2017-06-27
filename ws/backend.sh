#!/usr/bin/env bash

restart=${1:-yes}

echo "killing backend process (if exists)"
ps -ef | grep "dummy-this-is-mydig-backend" | awk '{print $2}' | xargs kill -9

if [ ${restart} != "no" ]; then
    echo "starting backend"
    nohup python ws.py --dummy-this-is-mydig-backend &
fi

echo "done"