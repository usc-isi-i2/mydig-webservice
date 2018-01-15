import requests
import rest
import urllib


 
class AggregateQueryProcessor(object):
    def __init__(self,request,project_name,config_fields,project_root_name,es):
        self.myargs = request.args
        self.intervals = ["day","month","week","year","quarter","hour","minute","second"]
        self.aggregations = ["min","max","avg","count","sum"]
        self.config_fields = config_fields.keys()
        self.config = config_fields
        self.es = es
        self.project_root_name = project_root_name
        self.project_name = project_name
        self.group_by=self.myargs.get("_group-by",None)
        self.aggregation = self.myargs.get("_aggregation","count")
        self.aggregation_field = self.myargs.get("_aggregation-field",None)
        self.interval = self.myargs.get("_interval","day")

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
        query = self._build_query()
        resp = self.es.search(self.project_name, self.project_root_name ,query, ignore_no_index=True)
        return rest.ok(resp)

    def validate_input(self):
        for key in self.myargs.keys():
            if not key.startswith("_"):
                if "/" in key:
                    if key.split('/')[0] not in self.config_fields:
                        return False
        if self.interval not in self.intervals:
            return False
        elif self.group_by is None or self.group_by not in self.config_fields:
            return False
        elif self.aggregation_field is not None and self.aggregation_field not in self.config_fields:
            return False
        elif self.aggregation not in self.aggregations:
            return False

        return True

    def _addGroupByClause(self):
        return "blah"

    def _addDateClause(self):
        date_clause = {
            self.group_by : {
                "date_histogram" : {
                    "field" : self.group_by,
                    "interval" : self.interval
                }
            }
        }
        return date_clause


    def _build_query(self):
        """
        Builds an ElasticSearch query from a simple spec of DIG fields and constraints.
        @param field_query_terms: List of field:value pairs.
        The field can end with "/value" or "/key" to specify where to do the term query.
        @type field_query_terms:
        @return: JSON object with a bool term query in the ElasticSearch DSL.
        @rtype: dict
        """
        
        query = {}
        if self.config[self.group_by]['type'] == "date":
            query = self._addDateClause()
        else:
            query = self._addGroupByClause()

        full_query = {
            "aggs": query
        }
        full_query['size'] = 0
        print full_query    
        return full_query

            