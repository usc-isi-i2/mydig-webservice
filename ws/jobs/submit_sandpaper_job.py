from manage_oozie_jobs import OozieJobs


if __name__ == '__main__':
    property_dict = dict()
    property_dict["user.name"] = "asingh"
    property_dict[
        "oozie.wf.application.path"] = "hdfs://memex:8020/user/worker/summer_evaluation_2017/workflows/sandpaper/"
    property_dict["jobTracker"] = "memex-rm.xdata.data-tactics-corp.com:8032"
    property_dict["nameNode"] = "hdfs://memex"
    property_dict["oozie.use.system.libpath"] = "True"
    property_dict["INPUT"] = "/user/worker/etk/etk_out/2014-2"
    property_dict["OUTPUT"] = "/user/worker/etk/sandpaper_out/2014-2"
    property_dict["INDEX"] = "dig-etk-search-10"
    property_dict["DOC"] = "ads"
    property_dict["ES_ID"] = "doc_id"
    oozie_url = "http://10.1.94.54:11000/oozie"
    oj = OozieJobs(oozie_url=oozie_url)
    r = oj.submit_oozie_jobs(property_dict)
    print r.content
