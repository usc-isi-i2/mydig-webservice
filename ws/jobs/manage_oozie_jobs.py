# Memex cluster oozie url - http://10.1.94.54:11000/oozie

import requests


class OozieJobs(object):
    def __init__(self, oozie_url='http://localhost:11000/oozie'):
        self.oozie_url = oozie_url

    def submit_oozie_jobs(self, config_xml):
        oozie_url = self.oozie_url + "/v1/jobs"

        # open files in binary mode
        # config_xml = codecs.open('config.xml, 'r')
        files = {'file': config_xml}
        response = requests.post(oozie_url, files=files)
        return response

    def manage_job(self, job_id, action):
        # action can be 'start', 'suspend', 'resume', 'kill' and 'rerun'
        # curl - i - X PUT "http://localhost:11000/oozie/v1/job/0000000-130524111605784-oozie-rkan-W?action=kill"
        oozie_url = '{}/v1/job/{}?action={}'.format(self.oozie_url, job_id, action)
        response = requests.put(oozie_url)
        return response

"""
Sample config.xml
<configuration>
<property>
        <name>user.name</name>
        <value>rkanter</value>
    </property>
<property>
        <name>oozie.wf.application.path</name>
        <value>${nameNode}/user/${user.name}/${examplesRoot}/apps/no-op</value>
    </property>
<property>
        <name>queueName</name>
        <value>default</value>
    </property>
<property>
        <name>nameNode</name>
        <value>hdfs://localhost:8020</value>
    </property>
<property>
        <name>jobTracker</name>
        <value>localhost:8021</value>
    </property>
<property>
        <name>examplesRoot</name>
        <value>examples</value>
    </property>
</configuration>
"""