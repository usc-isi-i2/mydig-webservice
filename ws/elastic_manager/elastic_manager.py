import json
from elasticsearch import Elasticsearch
form elasticsearch import helpers
import requests

class ES(object):
    def __init__(self, es_url):
        self.es_url = es_url
        self.es = Elasticsearch([es_url], show_ssl_warnings=False)

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
                    "any": "data" + json.dumps(doc),
                }
            }
            for doc in docs
            ]

        helpers.bulk(self.es, actions)