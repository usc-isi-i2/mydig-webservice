import json
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch import TransportError
import requests

class ES(object):
    def __init__(self, es_url, http_auth=None):
        self.es_url = es_url
        self.es = Elasticsearch([es_url], show_ssl_warnings=False, http_auth=http_auth)

    def load_data(self, index, doc_type, doc, doc_id):
        # import certifi
        #
        # es = Elasticsearch(
        #     ['localhost', 'otherhost'],
        #     http_auth=('user', 'secret'),
        #     port=443,
        #     use_ssl=True
        # )
        try:
            return self.es.index(index=index, doc_type=doc_type, body=doc, id=doc_id)
        except Exception as e:
            # try once more
            try:
                return self.load_data(index, doc_type, doc, doc_id)
            except Exception as e:
                print e
                return None

    def create_index(self, index_name, es_mapping):
        command = self.es_url + "/" + index_name
        return requests.put(command, data=es_mapping, verify=False)

    def create_alias(self, alias_name, indices):
        url = self.es_url + "/_aliases"
        command = {"actions": [
            {"remove": {"index": "*", "alias": alias_name}},
            {"add": {"indices": indices, "alias": alias_name}}
        ]}
        return requests.post(url, data=json.dumps(command))

    def load_bulk(self, index, doc_type, doc_id, docs):
        actions = [
            {
                "_index": index,
                "_type": doc_type,
                "_id": doc[doc_id],
                "_source": {
                    json.dumps(doc),
                }
            }
            for doc in docs
            ]

        helpers.bulk(self.es, actions)

    def retrieve_doc(self, index, doc_type, ids):
        if not isinstance(ids, list):
            ids = [ids]
        query = "{\"query\": {\"ids\": {\"values\":" + json.dumps(ids) + "}}}"
        print query
        try:
            return self.es.search(index=index, doc_type=doc_type, body=query, filter_path=['hits.hits._source'])
        except:
            # try once more
            try:
                return self.es.search(index=index, doc_type=doc_type, body=query, filter_path=['hits.hits._source'])
            except Exception as e:
                print e
                return None

    def search(self, index, doc_type, query, ignore_no_index=False):
        # print query
        try:
            return self.es.search(index=index, doc_type=doc_type, body=query,
                                  filter_path=['hits.hits._source', 'hits.hits._id', 'aggregations'])
        except TransportError as e:
            if e.error != 'index_not_found_exception' and ignore_no_index:
                print e
        except Exception as e:
            print e
            return None

if __name__ == '__main__':
    es = ES('http://10.1.94.103:9201')
    print es.retrieve_doc('dig-etk-gt','ads', ["092F55350A6125D8550D7652F867EBB9EB027C8EADA2CC1BAC0BEB1F48FE6D2B","33A5467DEA140814ED4C3A65EEB638029F4986EA7D7685E9D5957C3E5337C4EB"])