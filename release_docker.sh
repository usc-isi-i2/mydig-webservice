#!/usr/bin/env bash

opt="${1}"

source ./VERSION

if [ "$opt" == "build" ]; then
    echo "building image..."
    docker build --build-arg ETK_VERSION=${ETK_VERSION} -t uscisii2/mydig_ws:${MYDIG_WS_VERSION} .
elif [ "$opt" == "push" ]; then
    echo "pushing image..."
    docker push uscisii2/mydig_ws:${MYDIG_WS_VERSION}
elif [ "$opt" == "tag" ]; then
    echo "tagging..."
    git tag ${MYDIG_WS_VERSION}
fi



