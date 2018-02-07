import json
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch import TransportError
import requests

class ES(object):
    def __init__(self, es_url, http_auth=None):
        self.es_url = es_url
        self.es = Elasticsearch([es_url], show_ssl_warnings=False, http_auth=http_auth,retry_on_timeout=True)

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

    def search(self, index, doc_type, query, ignore_no_index=False, **other_params):
        # print query
        try:
            return self.es.search(index=index, doc_type=doc_type, body=query, **other_params)
        except TransportError as e:
            if e.error != 'index_not_found_exception' and ignore_no_index:
                print e
        except Exception as e:
            print e

    def es_search(self, index, doc_type, query, scroll, ignore_no_index=False, **other_params):
        # print query
        if not scroll:
            try:
                return self.es.search(index=index, doc_type=doc_type, body=query, **other_params)
            except Exception as e:
                return e
        else:
            #Initiating scroll
            try:
                total_docs = query['size']
                query['size'] = 0
                query['from'] = 0
                data = self.es.search(index=index, doc_type=doc_type, body=query,scroll='1m',size=1000, **other_params)
                print "starting scroll"
                docs = list(data['hits']['hits'])
                docs_count = len(data['hits']['hits'])
                print "Init docs" + str(docs_count)
                sid = data['_scroll_id']
                scroll_size = len(data['hits']['hits'])
                while scroll_size > 0 or docs_count > total_docs:
                    new_data = self.es.scroll(sid,scroll='1m')
                    sid = data['_scroll_id']
                    docs.append(list(new_data['hits']['hits']))
                    scroll_size = len(new_data['hits']['hits'])
                    docs_count = docs_count + scroll_size

                data['hits']['hits'] = docs[:total_docs]
                data['hits']['total'] = docs_count
                print "scroll complete with " + str(docs_count)
                return data
            except Exception as e:
                return e
            


    def mget(self,index,doc_type,body):
        try:
            return self.es.mget(index=index,doc_type=doc_type,body=body)
        except TransportError as e:
            if e.error != 'index_not_found_exception':
                print e
        except Exception as e:
            print e

if __name__ == '__main__':
    es = ES('http://10.1.94.103:9201')
    print es.retrieve_doc('dig-etk-gt','ads', ["092F55350A6125D8550D7652F867EBB9EB027C8EADA2CC1BAC0BEB1F48FE6D2B","33A5467DEA140814ED4C3A65EEB638029F4986EA7D7685E9D5957C3E5337C4EB"])