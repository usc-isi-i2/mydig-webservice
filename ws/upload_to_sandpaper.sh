#!/bin/bash

sandpaper_url="$1"
ws_url="$2"
project_name="$3"
index="$4"
type="$5"
working_dir="$6"


status_code=$(curl -s -o /dev/null -w "%{http_code}"  \
    -XPUT "{$sandpaper_url}/mapping?url=${ws_url}&project=${project_name}&index=${index}")
if [ $(( ${status_code}/100 )) -ne 2 ]; then
    exit ${status_code}
fi

status_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Content-Type: application/json" -XPOST \
    --data-binary "@${working_dir}/etk_out.jl" \
    "${sandpaper_url}/indexing?index=${index}" \
    -o /dev/null -w '%{http_code}\n' -s)
exit ${status_code}
