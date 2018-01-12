import requests
import rest
import urllib

class ConjuctiveQueryProcessor(object):
	def __init__(self,request,project_name,config_fields,project_root_name,es):
		self.myargs = request.args
		self.field_names = self.myargs.get("_fields",None)
		self.num_results =  self.myargs.get("_size",20)
		self.ordering = self.myargs.get("_order-by",None)
		self.page = self.myargs.get("_page",0)
		self.verbosity = self.myargs.get("_verbosity","full")
		self.response_format = self.myargs.get("_format","json")
		self.config_fields = config_fields
		self.es = es
		self.project_root_name = project_root_name
		self.project_name = project_name
		self.nested_query = self.myargs.get("_dereference",None)
		self.KG_PREFIX = 'knowledge_graph'
		self.SOURCE = '_source'
		self.stats = self.myargs.get("_statistics","yes")

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
		res = self.es.search(self.project_name, self.project_root_name ,query, ignore_no_index=True)
		res_filtered = self.filter_response(res,self.field_names)
		resp={}
		if self.nested_query is not None and len(res_filtered['hits']['hits']) > 0:
			res_filtered = self.setNestedDocuments(res_filtered)
		if self.response_format =="json_lines":
			return rest.ok('\n'.join(str(x) for x in res_filtered['hits']['hits']))
		else:
			if self.verbosity == "minimal":
				if self.field_names is None:
					self.field_names = ','.join(self.config_fields)
				response_docs = self.minify_response(res_filtered,self.field_names)
				resp['hits']={}
				resp['hits']['hits'] = response_docs
				if not self.stats == "no":
					resp['hit_count'] = res_filtered['hits']['total']
					resp['execution_time'] = res_filtered['took']
			else:
				resp = res_filtered

		return rest.ok(resp)

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
					temp_id = json_doc[self.SOURCE][self.KG_PREFIX][field][0]['value']
					if temp_id not in ids_to_query[field]:
						ids_to_query[field].append(temp_id)
				except Exception as e: 
					print e
					pass
		result_map = self.executeNestedQuery(ids_to_query)
		for json_doc in resp['hits']['hits']:
			for field in list_of_fields:
				try:
					temp_id = json_doc[self.SOURCE][self.KG_PREFIX][field][0]['value']
					if temp_id in result_map:
						new_list = []
						new_doc = json_doc[self.SOURCE][self.KG_PREFIX][field][0]
						new_doc['knowledge_graph'] = result_map[temp_id][self.SOURCE][self.KG_PREFIX]
						new_list.append(new_doc)
						json_doc[self.SOURCE][self.KG_PREFIX][field]= new_list
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
			if len(resp['docs']) > 0:
				for json_doc in resp['docs']:
					result_map[json_doc['_source']['document_id']] = json_doc
		return result_map


	def validate_input(self):
		for key in self.myargs.keys():
			if not key.startswith("_"):
				if "/" in key:
					if key.split('/')[0] not in self.config_fields:
						return False
				elif "$" in key:
					if key.split('$')[0] not in self.config_fields:
						return False
				elif "." in key:
					continue
				elif key not in self.config_fields:
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
					new_json = {}
					if 'data' in json_doc[self.SOURCE][self.KG_PREFIX][field][0].keys():
						new_json['value'] = json_doc[self.SOURCE][self.KG_PREFIX][field][0]['data']
					else:
						new_json['value'] = json_doc[self.SOURCE][self.KG_PREFIX][field][0]['value']
					if self.KG_PREFIX in json_doc[self.SOURCE][self.KG_PREFIX][field][0].keys():
						nested_kg = json_doc[self.SOURCE][self.KG_PREFIX][field][0][self.KG_PREFIX]
						min_nested_kg = {}
						for inner_field in nested_kg.keys():
							nest_list = []
							nest_json = {}
							if 'data' in nested_kg[inner_field][0].keys():
								nest_json['value'] = nested_kg[inner_field][0]['data'] 
							else:
								nest_json['value'] = nested_kg[inner_field][0]['value']
							nest_list.append(nest_json)
							nested_kg[inner_field] = nest_list
						new_json[self.KG_PREFIX] = nested_kg
					new_list.append(new_json)
					minidoc[field] = new_list
				except Exception as e:
					pass
			minified_docs.append(minidoc)
		return minified_docs

	def generate_match_clause(self,term,args):
		'''
			This function generates match clauses which are inserted into the must part of the conjuctive query
		'''
		extraction = dict()
		must_clause = dict()
		if "/" in term:
			extraction['field_name'],rest = term.split('/')
			extraction['valueorkey'] = rest
		elif "." in term:
			extraction['field_name'],rest = term.split('.')
			extraction['valueorkey'] = rest
		else:
			extraction['field_name'] = term
			extraction['valueorkey'] = "value"
		if "/" in term:
			must_clause = {
				"match": {
					"knowledge_graph." + extraction['field_name'] + "." + extraction['valueorkey']: urllib.unquote(args[term])
				}
			}
		elif "." in term:
			must_clause = {
				"match": {
					"knowledge_graph." + extraction['field_name'] + "__" + extraction['valueorkey']: urllib.unquote(args[term])
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
		self.page = int(self.page)
		clause_list = []
		for query_term in self.myargs:
			if not query_term.startswith("_") and "$" not in query_term:
				clause_list.append(self.generate_match_clause(query_term,self.myargs))
			elif not query_term.startswith("_"):
				clause_list.append(self.generate_range_clause(query_term,self.myargs))
		full_query = {
			"query": {
				"bool": {
					querytype: clause_list
				}
			}
		}
		full_query['size'] = self.num_results
		full_query['from'] = self.page*self.num_results
		if self.ordering is not None:
			full_query['sort'] = self.get_sort_order()
		print full_query    
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
				for field in json_doc['_source']['knowledge_graph'].keys():
					if field not in fields:
						del json_doc['_source']['knowledge_graph'][field]
			resp['hits']['hits'] = docs
			return resp
			