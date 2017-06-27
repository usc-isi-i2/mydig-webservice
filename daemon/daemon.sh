#!/usr/bin/env bash
# run it in etk_env

restart=${1:-yes}

echo "killing daemon process (if exists)"
ps -ef | grep "dummy-this-is-mydig-daemon" | awk '{print $2}' | xargs kill -9

if [ ${restart} != "no" ]; then
    echo "starting daemon"
    nohup python daemon.py --dummy-this-is-mydig-daemon &
fi

echo "done"