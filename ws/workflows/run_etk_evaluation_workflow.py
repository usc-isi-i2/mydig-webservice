from optparse import OptionParser
from pyspark import SparkContext, SparkConf, StorageLevel
import json
from etk.core import Core
import codecs
from elastic_manager import ES
from initClassifiers import ProcessClassifier
__author__ = 'amandeep'


def load_into_es(es_index, es_doc_type, doc_id,output_rdd):
    es_write_conf = {
        "es.nodes": "10.1.94.70,10.1.94.68,10.1.94.69",
        "es.port": "9200",
        "es.nodes.discover": "false",
        'es.nodes.wan.only': "true",
        "es.resource": es_index + '/' + es_doc_type,  # use domain as `doc_type`
        "es.http.timeout": "30s",
        "es.http.retries": "20",
        "es.batch.write.retry.count": "20",  # maximum number of retries set
        "es.batch.write.retry.wait": "300s",  # on failure, time to wait prior to retrying
        "es.batch.size.entries": "200000",  # number of docs per batch
        "es.mapping.id": doc_id,  # use `uri` as Elasticsearch `_id`
        "es.input.json": "true"
    }
    es_write_man = ES(sc, conf, es_write_conf=es_write_conf)
    es_input_rdd = output_rdd.partitionBy(20)
    es_write_man.rdd2es(es_input_rdd)


if __name__ == '__main__':
    compression = "org.apache.hadoop.io.compress.GzipCodec"

    parser = OptionParser()
    (c_options, args) = parser.parse_args()
    workspace_directory = args[0]
    # output_path = args[1]
    extraction_config_path = args[1]
    es_read_index = args[2]
    es_read_doc_type = args[3]
    es_write_index = args[4]
    es_write_doc_type = args[5]
    classifier_properties_path = args[6]
    # start_date = args[5]
    # end_date = args[6]
    parser.add_option("-p", "--num_partitions", dest="num_partitions", type="int", default=1000)
    parser.add_option("-e", "--esinput", dest="esinput", default=False, action="store_true")
    parser.add_option("-h", "--hdfsinput", dest="hdfsinput", default=False, action="store_true")
    parser.add_option("-c", "--contentextraction", dest="contentextraction", default=False, action="store_true")
    parser.add_option("-d", "--dataextraction", dest="dataextraction", default=False, action="store_true")

    num_partitions = c_options.num_partitions
    esinput = c_options.esinput
    hdfsinput = c_options.hdfsinput
    contentextraction = c_options.contentextraction
    dataextraction = c_options.dataextraction

    sc = SparkContext(appName="ETK-Evaluation-End-to-End")
    conf = SparkConf()

    # start_time_datetime_query = dateutil.parser.parse(start_date)
    # start_time_query_iso = str(start_time_datetime_query.isoformat())
    # end_time_datetime_query = dateutil.parser.parse(end_date)
    # end_time_query_iso = str(end_time_datetime_query.isoformat())

    """Part 1: Get the data"""
    if esinput:
        es_read_conf = dict()
        es_read_conf['es.resource'] = es_read_index + "/" + es_read_doc_type
        es_read_conf['es.nodes'] = "cdr-es.istresearch.com" + ":" + str(9200)
        es_read_conf['es.index.auto.create'] = "no"
        es_read_conf['es.net.http.auth.user'] = "cdr-memex"
        es_read_conf['es.net.http.auth.pass'] = "5OaYUNBhjO68O7Pn"
        es_read_conf['es.net.ssl'] = "true"
        es_read_conf['es.nodes.discovery'] = "false"
        es_read_conf['es.http.timeout'] = "1m"
        es_read_conf['es.http.retries'] = "1"
        es_read_conf['es.nodes.client.only'] = "false"
        es_read_conf['es.nodes.wan.only'] = "true"

        # query = "{\"query\": {\"filtered\": {\"query\": {\"match_all\": {}},\"filter\": {\"and\": {\"filters\": [{\"missing\": {\"field\": \"obj_parent\"}},{\"exists\": {\"field\": \"doc_id\"}},{\"range\": {\"timestamp\": {\"gte\": \"" + start_time_query_iso + "\"" + ",\"lt\": \"" + end_time_query_iso + "\"}}}]}}}}}"
        query = "{\"query\": {\"filtered\": {\"query\": {\"match_all\": {}},\"filter\": {\"and\": {\"filters\": [{\"missing\": {\"field\": \"obj_parent\"}},{\"exists\": {\"field\": \"doc_id\"}}]}}}}}"

        es_read_man = ES(sc, conf, es_read_conf=es_read_conf)
        input_rdd = es_read_man.es2rdd(query)
        input_rdd.mapValues(json.dumps).saveAsSequenceFile(workspace_directory + "/input-docs",
                                                           compressionCodecClass=compression)
        input_rdd = None
        input_rdd = sc.sequenceFile(workspace_directory + "/input-docs").partitionBy(num_partitions).mapValues(
            json.loads)
    elif hdfsinput:
        input_rdd = sc.sequenceFile(workspace_directory + "/input-docs").partitionBy(num_partitions).mapValues(
            json.loads)
    else:
        raise "Specify a input parameter: either hdfs or cdr"

    """Part 2: Run etk"""
    extraction_config = json.load(codecs.open(extraction_config_path))
    """First run the content extraction and save the results,
    so that we can data extraction multiple times without content extraction part"""
    content_extraction_config = extraction_config
    content_extraction_config.pop('data_extraction', None)
    c = Core(extraction_config=content_extraction_config)
    processed_rdd = input_rdd.mapValues(lambda x: c.process(x))
    processed_rdd.mapValues(json.dumps).saveAsSequenceFile(workspace_directory + "/content_extracted",
                                                           compressionCodecClass=compression)
    processed_rdd = None
    processed_rdd = sc.sequenceFile(workspace_directory + "/content_extracted").mapValues(json.loads)

    data_extraction_config = extraction_config.pop('content_extraction', None)
    c = Core(extraction_config=data_extraction_config)
    processed_rdd = input_rdd.mapValues(lambda x: c.process(x, create_knowledge_graph=True))


    """Part 3: run classifier"""
    extraction_classifiers = ['city', 'ethnicity', 'hair_color', 'name', 'eye_color']

    classifier_processor = ProcessClassifier(extraction_classifiers)

    classifier_properties = json.load(codecs.open(classifier_properties_path, 'r'))

    classified_rdd = processed_rdd.mapValues(classifier_processor.classify_extractions).mapValues(json.dumps)

    classified_rdd.saveAsSequenceFile(workspace_directory + "/etk-processed", compressionCodecClass=compression)
    classified_rdd = None
    classified_rdd = sc.sequenceFile(workspace_directory + "/etk-processed")
    load_into_es(es_write_index, es_write_doc_type, 'doc_id', classified_rdd)

