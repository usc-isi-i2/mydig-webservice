#!/bin/bash

page_path="$1"
working_dir="$2"
conda_bin_path="$3"
etk_path="$4"

data_path="${working_dir}/etk_input.jl"
if [ ! -f ${data_path} ]; then
    data_path="${working_dir}/consolidated_data.jl"
    cat ${page_path}/* > ${data_path}
fi

source ${conda_bin_path}/activate etk_env
python ${etk_path}/etk/run_core.py \
    -i ${data_path} \
    -o ${working_dir}/etk_out.jl \
    -c ${working_dir}/etk_config.json > ${working_dir}/etk_stdout.txt
last_exit_code=$?

if [ ${last_exit_code} == 0 ]; then
    cp "${working_dir}/etk_out.jl" "${working_dir}/etk_input.jl"
fi

exit ${last_exit_code}
