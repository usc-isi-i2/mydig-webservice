#!/usr/bin/env bash
# run it in etk_env

restart=${1:-yes}

echo "killing daemon process (if exists)"
ps -ef | grep "dummy-this-is-mydig-daemon" | awk '{print $2}' | xargs kill -9

if [ ${restart} != "no" ]; then
    echo "starting daemon (ETK spaCy)"
    nohup python etk_spacy.py --dummy-this-is-mydig-daemon > nohup_etk_spacy.out &
    echo "starting daemon (ACHE)"
    nohup python ache_consumer.py --dummy-this-is-mydig-daemon > nohup_ache.out &
fi

echo "done"