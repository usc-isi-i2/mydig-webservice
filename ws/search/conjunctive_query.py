import requests
import urllib
import traceback,sys
import json
import rest
import re
from elasticsearch import RequestError
from flask import Response


class ConjunctiveQueryProcessor(object):
    def __init__(self,request,project_name,config_fields,project_root_name,es):
        self.myargs = request.args
        self.preprocess()
        self.field_names = self.myargs.get("_fields",None)
        self.num_results =  self.myargs.get("_size",20)
        self.ordering = self.myargs.get("_order-by",None)
        self.fr = self.myargs.get("_from",0)
        self.verbosity = self.myargs.get("_verbosity","es")
        self.response_format = self.myargs.get("_format","json")
        self.config_fields = config_fields.keys()
        self.config = config_fields
        self.es = es
        self.project_root_name = project_root_name
        self.project_name = project_name
        self.nested_query = self.myargs.get("_dereference",None)
        self.KG_PREFIX = 'knowledge_graph'
        self.SOURCE = '_source'
        self.group_by=self.myargs.get("_group-by",None)
        self.aggregation = self.myargs.get("_aggregation",None)
        self.aggregation_field = self.myargs.get("_aggregation-field",None)
        if self.aggregation_field is not None and self.aggregation is None:
            self.aggregation = "sum"
        self.interval = self.myargs.get("_interval","day")
        self.intervals = ["day","month","week","year","quarter","hour","minute","second"]
        self.aggregations = ["min","max","avg","count","sum"]

    def preprocess(self):
        for arg in self.myargs:
            arg = urllib.unquote(arg)
        return

    def process(self):
        '''
        This is the main function in this class. This calls several functions to validate input, set match clauses, set filter clauses
        set sort clauses and finally resolve any nested documents if needed. Finally this function returns the data as a json or json_lines
        joined by a '\n'
        '''
        valid_input = self.validate_input()
        if not valid_input:
            err_json = {}
            err_json['message'] = "Please enter valid query params. Fields must exist for the given project. If not sure, please access http://mydigurl/projects/<project_name>/fields API for reference"
            return rest.bad_request(err_json)
        query = self._build_query("must")
        res = None
        print query
        if self.num_results+self.fr > 10000:
            res = self.es.es_search(self.project_name, self.project_root_name ,query,True, ignore_no_index=True)
        else:
            res = self.es.es_search(self.project_name, self.project_root_name ,query,False, ignore_no_index=True)
        if type(res) == RequestError:
            return rest.bad_request(str(res))
        res_filtered = self.filter_response(res,self.field_names)
        resp={}
        if self.nested_query is not None and len(res_filtered['hits']['hits']) > 0:
            res_filtered = self.setNestedDocuments(res_filtered)
        if self.group_by is None:
            if self.verbosity == "minimal":
                if self.field_names is None:
                    self.field_names = ','.join(self.config_fields)
                resp = self.minify_response(res_filtered,self.field_names)
            elif self.verbosity == "full":
                resp = res_filtered['hits']['hits']
            else:
                resp = res_filtered
        else:
            resp = res_filtered
        if self.response_format =="json_lines":
            return Response(self.create_json_lines_response(resp),mimetype='application/x-jsonlines')
        return rest.ok(resp)

    def create_json_lines_response(self,resp):
        docs = resp if self.verbosity is not None and self.verbosity =="minimal" else resp['hits']['hits']
        json_lines = '\n'.join([json.dumps(x) for x in docs])
        return json_lines


    def setNestedDocuments(self,resp):
        '''
            This function is to query for the nested documents and retrieve them
            It attaches only the KG component of the nested document into the parent document. Expects a json response,
            returns a json resposne after dereferencing the required set of child documents. Can dereference multiple children 
            documents. 
            See readme for exact usage and details.
        '''          
        list_of_fields = self.nested_query.split(',')
        ids_to_query = {}
        for field in list_of_fields:
            ids_to_query[field] = []
        for json_doc in resp['hits']['hits']:
            for field in list_of_fields:
                try:
                    for nest_doc in json_doc[self.SOURCE][self.KG_PREFIX][field]:
                        temp_id = nest_doc['value']
                        if temp_id not in ids_to_query[field]:
                            ids_to_query[field].append(temp_id)
                except Exception as e: 
                    print e
                    pass
        result_map = self.executeNestedQuery(ids_to_query)
        if len(result_map.keys()) > 0:
            for json_doc in resp['hits']['hits']:
                for field in list_of_fields:
                    try:
                        for nest_doc in json_doc[self.SOURCE][self.KG_PREFIX][field]:
                            temp_id = nest_doc['value']
                            if temp_id in result_map:
                                nest_doc['knowledge_graph'] = result_map[temp_id][self.SOURCE][self.KG_PREFIX]
                    except Exception as e: 
                        print e
                        pass
        return resp


    def executeNestedQuery(self,idMap):
        '''
            A function to perform the mget search and retrieve the nested documents
        '''
        result_map = {}
        for key in idMap:
            query = {
            "ids" : idMap[key]
            }
            resp = self.es.mget(index=self.project_name,body=query,doc_type=self.project_root_name)
            if resp is not None and len(resp['docs']) > 0:
                for json_doc in resp['docs']:
                    result_map[json_doc['_source']['document_id']] = json_doc
        return result_map


    def validate_input(self):
        for key in self.myargs.keys():
            if not key.startswith("_"):
                if "." in key:
                    continue
                elif "/" in key:
                    if key.split('/')[0] not in self.config_fields:
                        return False
                elif "$" in key:
                    if key.split('$')[0] not in self.config_fields:
                        return False
                elif key not in self.config_fields:
                    return False
        if self.interval is not None:
            gp = re.search(r"(\d+d|\d+m|\d+s|\d+h)",self.interval)
            if gp is None and self.interval not in self.intervals:
                return False
        elif self.group_by is not None and "." not in self.group_by and self.group_by not in self.config_fields:
            return False
        elif self.aggregation_field is not None and "." not in self.aggregation_field and self.aggregation_field not in self.config_fields:
            return False
        elif self.aggregation is not None and self.aggregation not in self.aggregations:
            return False

        return True

    def minify_response(self,response,myargs):
        '''
            This function takes in the response in json format and minimizes the KG Component down to simple key,value pairs
            Also minimizes the KG component inside a particular nested field as well. 
        '''
        fields = myargs.split(',')
        docs = response['hits']['hits']
        minified_docs = []
        for json_doc in docs:
            minidoc = {}
            for field in fields:
                try:
                    new_list = []
                    for element in json_doc[self.SOURCE][self.KG_PREFIX][field]:
                        if self.KG_PREFIX in json_doc[self.SOURCE][self.KG_PREFIX][field][0].keys():
                            nested_doc = json.loads(json.dumps(json_doc[self.SOURCE][self.KG_PREFIX][field][0]))
                            nested_kg = nested_doc[self.KG_PREFIX]
                            min_nested_kg = {}
                            for inner_field in nested_kg.keys():
                                nest_list = []
                                for nested_element in nested_kg[inner_field]:
                                    if 'data' in nested_element.keys():
                                        nest_list.append(nested_element['data']) 
                                    else:
                                        nest_list.append(nested_element['value'])
                                nested_kg[inner_field] = nest_list
                            nested_doc_id = []
                            nested_doc_id.append(nested_doc['value'])
                            nested_kg['doc_id'] = nested_doc_id
                            new_list.append(nested_kg)
                        elif 'data' in element.keys():
                           new_list.append(element['data'])
                        else:
                           new_list.append(element['value'])
                    minidoc[field] = new_list
                except Exception as e:
                    # exc_type, exc_value, exc_traceback = sys.exc_info()
                    # lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                    # lines = ''.join(lines)
                    # print lines
                    pass
            doc_id = []
            doc_id.append(json_doc[self.SOURCE]['document_id'])
            minidoc['doc_id'] = doc_id
            minified_docs.append(minidoc)
        return minified_docs

    def generate_match_clause(self,term,args):
        '''
            This function generates match clauses which are inserted into the must part of the conjunctive query
        '''
        extraction = dict()
        must_clause = dict()
        if "/" in term:
            extraction['field_name'],rest = term.split('/')
            extraction['field_name'] = extraction['field_name'].replace(".","__")
            extraction['valueorkey'] = rest
        else:
            extraction['field_name'] = term
            extraction['field_name'] = extraction['field_name'].replace(".","__")
            extraction['valueorkey'] = "value"
        if "/" in term or "." in term:
            must_clause = {
                "match": {
                    "knowledge_graph." + extraction['field_name'] + "." + extraction['valueorkey']: urllib.unquote(args[term])
                }
            }
        else:
            must_clause = {
                "match": {
                    "knowledge_graph." + extraction['field_name'] + "." + extraction['valueorkey']: urllib.unquote(args[term])
                }
            }
        return must_clause

    def get_sort_order(self):
        '''
        This function generates order clauses for the query. It uses the member variables set in class to generate
        any order by clauses if needed. It looks for fields like field_name$desc or field_name$asc.
        '''
        sort_clauses = []
        field_prefix = "knowledge_graph."
        field_suffix = ".value"
        for order in self.ordering.split(','):
            order_key,order_val = order.split('$')
            if "." in order_key:
                order_key = order_key.replace(".","__")
            sort_clause =  { field_prefix + order_key + field_suffix : {"order" : order_val}}
            sort_clauses.append(sort_clause)
        return sort_clauses

    def generate_range_clause(self,term,args):
        '''
        This function converts filter operators such as field.name$desc into a sort clause,
        which can be used in our Elastic search query
        @input a single term of the form field.value$asc or field.value$desc and set of all input argument mappings.
        @output a filter_clause with the field.value and filter type.

        '''
        conversions = { "less-than": "lt", "less-equal-than" : "lte", "greater-than": "gt","greater-equal-than": "gte"}
        extracted_term = term.split('$')
        if "." in extracted_term[0]:
            extracted_term[0] = extracted_term[0].replace(".","__")
        range_clause = {
                    "range" : {
                         "knowledge_graph."+extracted_term[0]+".value" : {
                                 conversions[extracted_term[1]] : args[term]
                }
            }
        }
        return range_clause


    def _build_query(self,querytype):
        """
        Builds an ElasticSearch query from a simple spec of DIG fields and constraints.
        @param field_query_terms: List of field:value pairs.
        The field can end with "/value" or "/key" to specify where to do the term query.
        @type field_query_terms:
        @return: JSON object with a bool term query in the ElasticSearch DSL.
        @rtype: dict
        """
        self.num_results = int(self.num_results)
        self.fr = int(self.fr)
        clause_list = []
        for query_term in self.myargs:
            if not query_term.startswith("_") and "$" not in query_term:
                clause_list.append(self.generate_match_clause(query_term,self.myargs))
            elif not query_term.startswith("_"):
                clause_list.append(self.generate_range_clause(query_term,self.myargs))
        full_query = {}
        if len(clause_list) > 0:
            full_query['query'] = {
                "bool": {
                    querytype: clause_list
                }
            }

        full_query['size'] = self.num_results
        full_query['from'] = self.fr
        if self.ordering is not None:
            full_query['sort'] = self.get_sort_order()
        if self.group_by is not None:
            full_query['size'] = 0
            if "." not in self.group_by and self.config[self.group_by]['type'] == "date":
                query = self._addDateClause()
                full_query['aggs'] = query
            else:
                query = self._addGroupByClause()
                full_query['aggs'] = query
        return full_query

    def filter_response(self,resp,fields):
        '''
        This function takes a response from elasticSearch and keeps only the specified fields in the 'knowledge_graph' component
        @input : response from ES and fields specified in query
        @output : filter fields in _source.knowledge_graph basis fields specified by user
        '''
        if fields is None:
            return resp
        else:
            docs = resp['hits']['hits']
            for json_doc in docs:
                for field in json_doc[self.SOURCE][self.KG_PREFIX].keys():
                    if field not in fields:
                        del json_doc[self.SOURCE][self.KG_PREFIX][field]
            resp['hits']['hits'] = docs
            return resp
            
    def _addGroupByClause(self):
        if "." in self.group_by:
            params = self.group_by.split('.')
            self.group_by = params[0] + "__" + params[1]
        full_clause =  {
                  self.group_by: {
                   "terms": {
                    "field":  'knowledge_graph.'+self.group_by+'.key'
                }
            }
        }
        if self.aggregation_field is not None:
            if "." in self.aggregation_field:
                params = self.aggregation_field.split('.')
                self.aggregation_field = params[0] + "__" + params[1]
            agg_clause = {
                    self.aggregation_field: {
                     self.aggregation : {
                      "field": 'knowledge_graph.'+self.aggregation_field+'.key'
                    }
                }
            }
            full_clause['aggs'] = agg_clause
        return full_clause
        

    def _addDateClause(self):
        date_clause = {
            self.group_by : {
                "date_histogram" : {
                    "field" : 'knowledge_graph.'+self.group_by+'.key',
                    "interval" : self.interval
                }
            }
        }
        if self.aggregation_field is not None:
            if "." in self.aggregation_field:
                params = self.aggregation_field.split('.')
                self.aggregation_field = params[0] + "__" + params[1]
            agg_clause = {
                    self.aggregation_field: {
                     self.aggregation : {
                      "field": 'knowledge_graph.'+self.aggregation_field+'.key'
                    }
                }
            }
            date_clause[self.group_by]['aggs'] = agg_clause
        return date_clause
