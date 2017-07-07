# Memex cluster oozie url - http://10.1.94.54:11000/oozie

import requests


class OozieJobs(object):
    def __init__(self, oozie_url='https://oozie.memexproxy.com/'):
        self.oozie_url = oozie_url

    def submit_oozie_jobs(self, property_dict):
        oozie_url = self.oozie_url + "/v1/jobs?action=start"

        # open files in binary mode
        # config_xml = codecs.open('config.xml, 'r')
        headers = {'Content-Type': 'application/xml'}
        payload = OozieJobs.create_worfklow_xml(property_dict)
        print payload
        response = requests.post(oozie_url, data=payload, headers=headers)
        return response

    def manage_job(self, job_id, action):
        # action can be 'start', 'suspend', 'resume', 'kill' and 'rerun'
        # curl - i - X PUT "http://localhost:11000/oozie/v1/job/0000000-130524111605784-oozie-rkan-W?action=kill"
        oozie_url = '{}/v1/job/{}?action={}'.format(self.oozie_url, job_id, action)
        response = requests.put(oozie_url)
        return response

    @staticmethod
    def append_property_toXML(XML, name, value):
        XML += "<property><name>{}</name><value>{}</value></property>".format(name, value)
        return XML

    @staticmethod
    def create_worfklow_xml(property_dict):
        payload = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><configuration>"
        for key in property_dict.keys():
            payload = OozieJobs.append_property_toXML(payload, key, property_dict[key])
        payload += "</configuration>"
        return payload


if __name__ == '__main__':
    property_dict = dict()
    property_dict["user.name"] = "skaraman"
    property_dict["oozie.wf.application.path"] = "<hdfs_path>"
    property_dict["jobTracker"] = "memex-rm.xdata.data-tactics-corp.com:8032"
    property_dict["nameNode"] = "hdfs://memex"
    property_dict["DAYTOPROCESS"] = "2017-04-02"
    property_dict["TABLE_SHA1"] = "escorts_images_sha1_infos_ext_dev"
    property_dict["TABLE_UPDATE"] = "escorts_images_updates_dev"
    property_dict["ES_DOMAIN"] = "escorts"
    oj = OozieJobs()
    oj.submit_oozie_jobs(property_dict)
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
