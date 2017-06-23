#!/bin/bash

page_path="$1"
working_dir="$2"
conda_bin_path="$3"
etk_path="$4"

echo ${page_path}
exit 1

cat ${page_path}/* > ${working_dir}/consolidated_data.jl
source ${conda_bin_path}/activate etk_env
python ${etk_path}/etk/run_core.py -i ${working_dir}/consolidated_data.jl -o ${working_dir}/etk_out.jl -c
${working_dir}/etk_config.json > ${working_dir} > etk_stdout.txt

exit $?