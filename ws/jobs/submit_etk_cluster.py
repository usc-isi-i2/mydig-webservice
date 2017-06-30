from manage_oozie_jobs import OozieJobs
import json


def update_etk_lib_cluster(master_project_config, project_name):
    # TODO upload the dicts and other resources to cluster

    # TODO update the workflow.xml and upload to the /user/worker/summer_evaluation_2017/workflows/etk/

    # TODO update run.sh and upload to cluster

    return

def submit_etk_cluster(master_project_config, project_name):
    property_dict = dict()
    property_dict["user.name"] = "asingh"
    property_dict[
        "oozie.wf.application.path"] = "hdfs://memex:8020/user/worker/summer_evaluation_2017/workflows/etk/"
    property_dict["jobTracker"] = "memex-rm.xdata.data-tactics-corp.com:8032"
    property_dict["nameNode"] = "hdfs://memex"
    property_dict["oozie.use.system.libpath"] = "True"
    property_dict['INPUT'] = '/user/worker/summer_evaluation_2017/' + project_name + "/es/full"
    current_version = master_project_config['index']['version']
    property_dict['OUTPUT'] = '/user/worker/summer_evaluation_2017/' + project_name + "/etk_out/" + str(current_version)
    oozie_url = "http://10.1.94.54:11000/oozie"
    oj = OozieJobs(oozie_url=oozie_url)
    oj.submit_oozie_jobs(property_dict)
