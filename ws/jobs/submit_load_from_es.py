from manage_oozie_jobs import OozieJobs
from optparse import OptionParser
import json


def submit_es_job_cluster(project_master_config, project_name):
    """
    "sources": [
    {
      "end_date": "2017-06-23",
      "index": "memex-domains",
      "password": "",
      "start_date": "2017-06-01",
      "tlds": [
        "backpage.com",
        "liveescortreviews.com"
      ],
      "type": "escorts",
      "url": "https://cdr-es.istresearch.com:9200",
      "username": "cdr-memex"
    }
  ]
    """
    property_dict = dict()
    property_dict["user.name"] = "asingh"
    property_dict[
        "oozie.wf.application.path"] = "hdfs://memex:8020/user/worker/summer_evaluation_2017/workflows/load_from_es/"
    property_dict["jobTracker"] = "memex-rm.xdata.data-tactics-corp.com:8032"
    property_dict["nameNode"] = "hdfs://memex"
    property_dict["oozie.use.system.libpath"] = "True"

    # read from project_master_config
    # lets get on the assumption train: one sources to rule them all

    sources = project_master_config['sources'][0]
    property_dict['ES_INDEX'] = sources['index']
    property_dict['ES_DOC'] = sources['type']
    es_url = sources['url']
    vals = es_url.split(':')
    property_dict['ES_HOST'] = vals[1].replace('/', '').strip()
    property_dict['ES_PORT'] = vals[2].replace('/', '').strip()
    property_dict['ES_USER'] = sources['username']
    property_dict['ES_PASSWORD'] = sources['password']

    query = {"query": {"match_all": {}}}
    property_dict["QUERY"] = json.dumps(query).replace(" ", "").strip()
    es_output_path = '/user/worker/summer_evaluation_2017/' + project_name + "/es/full"
    property_dict["OUTPUT_PATH"] = es_output_path

    oozie_url = "http://10.1.94.54:11000/oozie"
    oj = OozieJobs(oozie_url=oozie_url)
    return oj.submit_oozie_jobs(property_dict)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-s", "--startDate", action="store", type="string", dest="startDate")
    parser.add_option("-e", "--endDate", action="store", type="string", dest="endDate")
    (c_options, args) = parser.parse_args()
    start_date = c_options.startDate
    end_date = c_options.endDate

    if start_date and end_date:
        query = {"query":
                     {"filtered":
                          {"query":
                               {"match_all": {}},
                           "filter":
                               {"and":
                                   {"filters":
                                       [
                                           {"missing": {"field": "obj_parent"}},
                                           {"exists": {"field": "doc_id"}},
                                           {"range": {"timestamp": {"gte": start_date,
                                                                    "lt": end_date
                                                                    }
                                                      }
                                            }
                                       ]
                                   }
                               }
                           }
                      }
                 }
    else:
        query = {"query": {"match_all": {}}}

    (c_options, args) = parser.parse_args()
    property_dict = dict()
    property_dict["user.name"] = "asingh"
    property_dict[
        "oozie.wf.application.path"] = "hdfs://memex:8020/user/worker/summer_evaluation_2017/workflows/load_from_es/"
    property_dict["jobTracker"] = "memex-rm.xdata.data-tactics-corp.com:8032"
    property_dict["nameNode"] = "hdfs://memex"
    property_dict["oozie.use.system.libpath"] = "True"
    property_dict["ES_DOC"] = "escorts"
    property_dict["ES_HOST"] = "cdr-es.istresearch.com"
    property_dict["ES_INDEX"] = "memex-domains"
    property_dict["ES_PASSWORD"] = "<PASSWORD>"
    property_dict["ES_PORT"] = "9200"
    property_dict["ES_USER"] = "cdr-memex"
    property_dict["OUTPUT_PATH"] = "/user/worker/summer_evaluation_2017/es/input"
    property_dict["QUERY"] = json.dumps(query).replace(" ", "").strip()
    oozie_url = "http://10.1.94.54:11000/oozie"
    oj = OozieJobs(oozie_url=oozie_url)
    oj.submit_oozie_jobs(property_dict)
