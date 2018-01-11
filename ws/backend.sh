#!/usr/bin/env bash

restart=${1:-yes}

echo "killing backend process (if exists)"
ps -ef | grep "tag-mydig-backend" | awk '{print $2}' | xargs kill -9

if [ ${restart} != "no" ]; then
    echo "starting backend"
    python -u ws.py --tag-mydig-backend &
fi

echo "done"