#!/usr/bin/env bash

restart=${1:-yes}

echo "killing frontend process (if exists)"
ps -ef | grep "dummy-this-is-mydig-frontend" | awk '{print $2}' | xargs kill -9


if [ ${restart} != "yes" ]; then
    echo "starting frontend"
    nohup python service.py --dummy-this-is-mydig-frontend &
fi