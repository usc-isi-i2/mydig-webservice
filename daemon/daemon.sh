#!/usr/bin/env bash
# run it in etk_env

restart=${1:-yes}

echo "killing daemon process (if exists)"
ps -ef | grep "dummy-this-is-mydig-daemon" | awk '{print $2}' | xargs kill -9

if [ ${restart} != "no" ]; then
    echo "starting daemon (ETK spaCy)"
    python -u etk_spacy.py --dummy-this-is-mydig-daemon &
#    echo "starting daemon (ACHE)"
#    python -u ache_consumer.py --dummy-this-is-mydig-daemon &
fi

echo "done"