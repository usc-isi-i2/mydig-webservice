import rest
import urllib
from conjunctive_query import ConjunctiveQueryProcessor
from response_converter import DigOutputProcessor, TimeSeries
import logging
from config import config

logger = logging.getLogger(config['logging']['name'])


class EventQueryProcessor(object):

    def __init__(self, project_name, config_fields, project_root_name, es, myargs=None):
        self.myargs = myargs if myargs else dict()
        self.config = config_fields
        self.es = es
        self.project_root_name = project_root_name
        self.project_name = project_name
        self.cquery = ConjunctiveQueryProcessor(self.project_name,
                                                self.config,
                                                self.project_root_name, self.es, myargs=self.myargs)
        self.field = self.myargs.get('_group-by', "event_date")
        self.agg = self.myargs.get('_interval', "month")
        self.agg_field = self.myargs.get('_aggregation-field', None)
        if self.agg_field is not None and "." in self.agg_field:
            self.agg_field = self.convert_to_nested_field(self.agg_field)
        if self.field is not None and "." in self.field:
            self.field = self.convert_to_nested_field(self.field)
        self.percent_change = True if '_percent_change' in self.myargs else False
        self.impute_method = self.myargs.get('_impute_method', 'previous')

    # def preprocess(self):
    #     for arg in self.request.args:
    #         arg = urllib.unquote(arg)
    #     return

    def convert_to_nested_field(self, field):
        params = field.split('.')
        return params[0] + "__" + params[1]

    def process_ts_query(self):
        """
        This is the main function in this class. This calls several functions to validate input, set match clauses, set filter clauses
        set sort clauses and finally resolve any nested documents if needed. Finally this function returns the data as a json or json_lines
        joined by a '\n'
        """
        valid_input = self.validate_input()
        if not valid_input:
            err_json = dict()
            err_json['message'] = "Please enter valid query params. Fields must exist for the given project. " \
                                  "If not sure, please access http://mydigurl/projects/<project_name>/fields API for " \
                                  "reference"
            return rest.bad_request(err_json)

        resp = self.cquery.process()
        if resp is None or resp[1] == 400:
            return resp
        try:
            resp = resp[0]
            if len(resp['hits']['hits']) > 0 and 'doc_id' in resp['hits']['hits'][0]['_source'].keys():
                docid = resp['hits']['hits'][0]['_source']['doc_id']
                argmap = dict()
                argmap['measure/value'] = docid
                argmap['_group-by'] = 'event_date'
                argmap['_interval'] = self.agg
                self.myargs = argmap
                newquery = ConjunctiveQueryProcessor(self.project_name, self.config,
                                                     self.project_root_name, self.es, myargs=self.myargs)
                resp = newquery.process()
                if resp[1] == 400:
                    return resp
                else:
                    resp = resp[0]
                logger.debug("Response for query is {}".format(resp))
                isDateAggregation = True if "." not in self.field and self.config[self.field]['type'] == "date" else False
                ts, dims = DigOutputProcessor(resp['aggregations'][self.field], self.agg_field, isDateAggregation).process()
                ts_obj = TimeSeries(ts, dict(), dims, percent_change=self.percent_change, impute_method=self.impute_method).to_dict()
                return rest.ok(ts_obj)
            else:
                return rest.not_found("Time series not found")
        except Exception as e:
            logger.exception("Exception encountered while performing time series query")
            return rest.bad_request("Enter valid query")

    def process_event_query(self):
        """
        This is the main function in this class. This calls several functions to validate input, set match clauses, set filter clauses
        set sort clauses and finally resolve any nested documents if needed. Finally this function returns the data as a json or json_lines
        joined by a '\n'
        """
        valid_input = self.validate_input()
        if not valid_input:
            err_json = dict()
            err_json['message'] = "Please enter valid query params. Fields must exist for the given project. " \
                                  "If not sure, please access http://mydigurl/projects/<project_name>/fields " \
                                  "API for reference"
            return rest.bad_request(err_json)
        try:
            resp = self.cquery.process()
            if resp[1] == 400:
                logger.warning("Request generated 4xx response. Check request again")
                return resp
            else:
                resp = resp[0]
            if resp is not None and len(resp['aggregations'][self.field]['buckets']) > 0:
                isDateAggregation = True if "." not in self.field and self.config[self.field]['type'] == "date" else False
                ts, dims = DigOutputProcessor(resp['aggregations'][self.field], self.agg_field, isDateAggregation).process()
                ts_obj = TimeSeries(ts, {}, dims, percent_change=self.percent_change,
                                        impute_method=self.impute_method).to_dict()
                return rest.ok(ts_obj)
            else:
                return rest.not_found("No Time series found for query")
        except Exception as e:
            logger.exception("Exception encountered while performing Event query")
            return rest.internal_error("Internal Error occured")

    def validate_input(self):
        field = self.myargs.get('_group-by', None)
        if field is None:
            return False
        elif "." not in field and field not in self.config.keys():
            return False

        return True
