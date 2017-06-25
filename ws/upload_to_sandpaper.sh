#!/bin/bash

sandpaper_url="$1"
ws_url="$2"
project_name="$3"
index="$4"
type="$5"
working_dir="$6"

curl -XPUT "{$sandpaper_url}/mapping?url=${ws_url}&project=${project_name}&index=${index}"
last_exit_code=$?
if [ ${last_exit_code} -ne 0 ]; then
    exit ${last_exit_code}
fi

curl -H "Content-Type: application/json" -XPOST \
    --data-binary "@${working_dir}/etk_out.jl" \
    "{$sandpaper_url}/indexing?index=${index}"
last_exit_code=$?
if [ ${last_exit_code} -ne 0 ]; then
    exit ${last_exit_code}
fi

curl -XPOST "{$sandpaper_url}/config?url=${ws_url}&project=${project_name}&index=${index}&type=${type}"
exit $?