import rest
import urllib
from conjunctive_query import ConjunctiveQueryProcessor
from response_converter import DigOutputProcessor, TimeSeries
import logging
import numbers

logger = logging.getLogger('mydig-webservice.log')


class EventQueryProcessor(object):
    def __init__(self, request, project_name, config_fields, project_root_name, es, percent_change=False):
        self.request = request
        self.preprocess()
        self.config = config_fields
        self.es = es
        self.project_root_name = project_root_name
        self.project_name = project_name
        self.cquery = ConjunctiveQueryProcessor(self.request, self.project_name,
                                                self.config,
                                                self.project_root_name, self.es)
        self.field = request.args.get('_group-by', "event_date")
        self.agg = request.args.get('_interval', "month")
        self.agg_field = request.args.get('_aggregation-field', None)
        if self.agg_field is not None and "." in self.agg_field:
            self.agg_field = self.convert_to_nested_field(self.agg_field)
        if self.field is not None and "." in self.field:
            self.field = self.convert_to_nested_field(self.field)
        self.percent_change = percent_change

    def preprocess(self):
        for arg in self.request.args:
            arg = urllib.unquote(arg)
        return

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
            err_json = {}
            err_json[
                'message'] = "Please enter valid query params. Fields must exist for the given project. If not sure, please access http://mydigurl/projects/<project_name>/fields API for reference"
            return rest.bad_request(err_json)

        resp = self.cquery.process()[0]
        if resp[1] == 400:
            return resp
        try:
            if len(resp['hits']['hits']) > 0 and 'doc_id' in resp['hits']['hits'][0]['_source'].keys():
                docid = resp['hits']['hits'][0]['_source']['doc_id']
                argmap = {}
                argmap['measure/value'] = docid
                argmap['_group-by'] = 'event_date'
                argmap['_interval'] = self.agg
                self.request.args = argmap
                newquery = ConjunctiveQueryProcessor(self.request, self.project_name, self.config,
                                                     self.project_root_name, self.es)
                resp = newquery.process()
                if resp[1] == 400:
                    return resp
                else:
                    resp = resp[0]
                logger.debug("Response for query is {}".format(resp))
                ts, dims = DigOutputProcessor(resp['aggregations'][self.field], self.agg_field).process()
                ts_obj = TimeSeries(ts, dict(), dims).to_dict()
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
            err_json = {}
            err_json[
                'message'] = "Please enter valid query params. Fields must exist for the given project. If not sure, please access http://mydigurl/projects/<project_name>/fields API for reference"
            return rest.bad_request(err_json)
        try:
            resp = self.cquery.process()
            if resp[1] == 400:
                logger.warning("Request generated 4xx response. Check request again")
                return resp
            else:
                resp = resp[0]
            if resp is not None and len(resp['aggregations'][self.field]['buckets']) > 0:
                if "." not in self.field and self.config[self.field]['type'] == "date":
                    ts, dims = DigOutputProcessor(resp['aggregations'][self.field], self.agg_field, True).process()
                    ts_obj = TimeSeries(ts, {}, dims).to_dict()
                else:
                    ts, dims = DigOutputProcessor(resp['aggregations'][self.field], self.agg_field, False).process()
                    ts_obj = TimeSeries(ts, {}, dims).to_dict()
                if self.percent_change:
                    ts_obj['ts'] = self.pct_change(ts_obj['ts'])
                return rest.ok(ts_obj)
            else:
                return rest.not_found("No Time series found for query")
        except Exception as e:
            logger.exception("Exception encountered while performing Event query")
            return rest.internal_error("Internal Error occured")

    def validate_input(self):
        field = self.request.args.get('_group-by', None)
        if field is None:
            return False
        elif "." not in field and field not in self.config.keys():
            return False

        return True

    @staticmethod
    def pct_change(ts):
        """
        This function calculates the percentage for the aggregations calculated by ES
        :param ts: ts as calculated by this class
        :return: ts with values as percentage change
        """
        new_ts = list()
        new_ts.append(ts[0])
        for i in range(len(ts) - 1):
            j = i + 1
            new_ts.append(EventQueryProcessor.calculate_change_tuples(ts[i], ts[j]))
        return new_ts

    @staticmethod
    def calculate_change_tuples(tup_a, tup_b):
        """

        :param tup_a: tuple with format ["2011-12-01T00:00:00.000Z",34]
        :param tup_b: tuple with format ["2011-12-01T00:00:00.000Z",67]
        :return: tup_b with updated value as the percentage change
        """
        if tup_a[1] == 0:
            return tup_b

        return tup_b[0], EventQueryProcessor.calculate_percent_change(tup_a[1], tup_b[1])

    @staticmethod
    def calculate_percent_change(value_a, value_b):
        """
        This function calculates the percentage change in from value_a to value_b
        :param value_a: valid number
        :param value_b: valid number
        :return: percentage change calculated according to formula: abs((a-b)/a)
        """
        if not (isinstance(value_a, numbers.Number) and isinstance(value_b, numbers.Number)):
            message = "Input parameters to the function \"calculate_percentage_change\" should be a valid number, " \
                      "but was instead: {} and {}".format(value_a, value_b)
            logger.exception(message)
            raise ValueError(message)

        if value_a == 0:
            raise ValueError('First parameter can not be zero')
        return abs((float(value_a) - float(value_b)) / float(value_a)) * 100
