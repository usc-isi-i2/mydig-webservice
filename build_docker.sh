#!/usr/bin/env bash

source ./VERSION

echo "building myDIG Web Service image..."
docker build --build-arg ETK_VERSION=${ETK_VERSION} -t uscisii2/mydig_ws:${MYDIG_WS_VERSION} .
