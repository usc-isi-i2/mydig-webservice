#!/usr/bin/env bash

conda_bin_path="$1"
spacy_input="$2"
field_name="$3"

source ${conda_bin_path}/activate etk_env
python run_spacy_rules.py --input ${spacy_input} --field ${field_name}

exit $?