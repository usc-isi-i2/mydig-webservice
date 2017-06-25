#!/usr/bin/env bash

echo "killing frontend process"
ps -ef | grep "dummy-this-is-mydig-frontend" | awk '{print $2}' | xargs kill -9
echo "restart frontend"
./nohup python service.py --dummy-this-is-mydig-frontend &