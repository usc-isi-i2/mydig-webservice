#!/bin/bash

page_path="$1"
working_dir="$2"
conda_bin_path="$3"
etk_path="$4"
num_processes="$5"

# prepare data source
#data_path="${working_dir}/etk_input.jl"
#if [ ! -f ${data_path} ]; then
    data_path="${working_dir}/consolidated_data.jl"
    cat ${page_path}/* > ${data_path}
#fi

# initiate etk env
source ${conda_bin_path}/activate etk_env

# serial
#python ${etk_path}/etk/run_core.py \
#    -i ${data_path} \
#    -o ${working_dir}/etk_out.jl \
#    -c ${working_dir}/etk_config.json > ${working_dir}/etk_stdout.txt


# create output tmp dir
if [ ! -d ${working_dir}/tmp ]; then
    mkdir ${working_dir}/tmp
fi

# clean previous outputs and progress
rm ${working_dir}/tmp/output_chunk_*
rm ${working_dir}/etk_progress

# create progress file
num_of_docs=$(wc -l ${working_dir}/consolidated_data.jl | awk '{print $1}')
while true; do sleep 5; \
    wc -l ${working_dir}/tmp/output_chunk_* | tail -n 1 | awk -v total=$num_of_docs '{print total" "$1}' \
     > ${working_dir}/etk_progress; \
done &
progress_job_id=$!

# run etk parallelly
python ${etk_path}/etk/run_core.py \
    -i ${data_path} \
    -o ${working_dir}/tmp \
    --dummy-this-is-mydig-backend-etk-process
    -c ${working_dir}/etk_config.json \
    -m -t ${num_processes} > ${working_dir}/etk_stdout.txt
last_exit_code=$?

# close progress background job
kill ${progress_job_id}

if [ ${last_exit_code} == 0 ]; then
    exit ${last_exit_code}
fi

# concatenate outputs
cat ${working_dir}/tmp/* > ${working_dir}/etk_out.jl

#if [ ${last_exit_code} == 0 ]; then
#    cp "${working_dir}/etk_out.jl" "${working_dir}/etk_input.jl"
#fi

exit ${last_exit_code}
