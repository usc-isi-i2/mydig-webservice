import requests
import rest
import urllib
import traceback,sys
from conjunctive_query import ConjunctiveQueryProcessor
from response_converter import DigOutputProcessor,TimeSeries
import json,sys,traceback


class EventQueryProcessor(object):
    def __init__(self,request,project_name,config_fields,project_root_name,es):
        self.request = request
        self.config = config_fields
        self.es = es
        self.project_root_name = project_root_name
        self.project_name = project_name
        self.cquery = ConjunctiveQueryProcessor(self.request, self.project_name,
                                          self.config,
                                          self.project_root_name, self.es)
        self.field = request.args.get('_group-by',"event_date")
        self.agg = request.args.get('_interval',"month")
        self.agg_field = request.args.get('_aggregation-field',None)
        if "." in self.agg_field:
            self.agg_field = self.convert_to_nested_field(self.agg_field)
        if "." in self.field:
            self.field = self.convert_to_nested_field(self.field)

    def convert_to_nested_field(self,field):
        params = field.split('.')
        return params[0] + "__" + params[1]

    def process_ts_query(self):
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

        resp = self.cquery.process()[0]
        try:
            if len(resp['hits']['hits']) > 0 and 'doc_id' in resp['hits']['hits'][0]['_source'].keys():
                docid = resp['hits']['hits'][0]['_source']['doc_id']
                argmap = {}
                argmap['measure/value'] = docid 
                argmap['_group-by'] = 'event_date'
                argmap['_interval'] = self.agg
                self.request.args = argmap
                newquery = ConjunctiveQueryProcessor(self.request, self.project_name, self.config, self.project_root_name, self.es)
                resp = newquery.process()[0]
                print resp
                ts,dims = DigOutputProcessor(resp['aggregations'][self.field],self.agg_field).process()
                ts_obj = TimeSeries(ts, dict(), dims).to_dict()
                return rest.ok(ts_obj)
            else:
                return rest.not_found("Time series not found")
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            lines = ''.join(lines)
            print lines
            return rest.bad_request("Enter valid query")

    def process_event_query(self):
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

        resp = self.cquery.process()[0]
        ts,dims = DigOutputProcessor(resp['aggregations'][self.field],self.agg_field).process()
        ts_obj = TimeSeries(ts, {}, dims).to_dict()
        return rest.ok(ts_obj)

    def validate_input(self):
        field = self.request.args.get('_group-by',None)
        if field is None:
            return False
        elif "." not in field and not self.config[field]['type'] == "date":
            return False

        return True