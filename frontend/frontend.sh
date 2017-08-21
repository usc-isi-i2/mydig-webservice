#!/usr/bin/env bash

restart=${1:-yes}

echo "killing frontend process (if exists)"
ps -ef | grep "tag-mydig-frontend" | awk '{print $2}' | xargs kill -9

if [ ${restart} != "no" ]; then
    echo "starting frontend"
    nohup python service.py --tag-mydig-frontend &
fi

echo "done"