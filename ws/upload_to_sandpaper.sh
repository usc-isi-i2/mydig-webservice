#!/bin/bash

sandpaper_url="$1"
ws_url="$2"
project_name="$3"
index="$4"
type="$5"
working_dir="$6"

# create index
status_code=$(curl -s -o /dev/null -w "%{http_code}"  \
    -XPUT "{$sandpaper_url}/mapping?url=${ws_url}&project=${project_name}&index=${index}")
echo "[sandpaper] create index: ${status_code}"
if [ $(( ${status_code}/100 )) -ne 2 ]; then
    exit ${status_code}
fi

# split file
if [ ! -d ${working_dir}/etk_out_part ]; then
    mkdir ${working_dir}/etk_out_part
fi
split -l 1000 --additional-suffix=.jl "${working_dir}/etk_out.jl" "${working_dir}/etk_out_part/part_"

# upload files
for f in ${working_dir}/etk_out_part/part_* ; do
    echo "[sandpaper] uploading ${f}"
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Content-Type: application/json" -XPOST \
        --data-binary "@${f}" \
        "${sandpaper_url}/indexing?index=${index}" \
        -o /dev/null -w '%{http_code}\n' -s)
    echo "[sandpaper] upload data: ${status_code}"
    if [ $(( ${status_code}/100 )) -ne 2 ]; then
        exit ${status_code}
    fi
done
exit ${status_code}