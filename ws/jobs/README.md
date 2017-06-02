# Parameters in submit_load_from_es.py
1. The workflow xml should at the path `hdfs://memex:8020/user/worker/summer_evaluation_2017/workflows/load_from_es/` as defined at the line: 41 (`oozie.wf.application.path`)
2. The sample workflow for this job is at - `mydig-webservice/ws/workflows/workflow_definition/load_from_es/`
3. Before submitting, update the password at line 48
4. Make sure to update the output path of the job at line 51, the property `OUTPUT_PATH`

## Submit Load data from ES job
`python submit_load_from_es.py`

to get the data for a particular date range,

`python submit_load_from_es.py -s <START_DATE> -e <END_DATE>`

Dates in isoformat, eg: '2017-06-01T00:00:00'
