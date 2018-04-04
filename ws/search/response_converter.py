import numbers


class TimeSeries(object):
    def __init__(self, ts, metadata, dimensions, percent_change=False, impute_method='previous'):
        self.ts = ts
        self.metadata = metadata
        self.dimensions = dimensions
        self.percent_change = percent_change
        self.impute_method = impute_method

        self.impute_values()
        if self.percent_change:
            self.ts = self.pct_change(self.ts)
        self.ts = self.impute_values()

    def to_dict(self):
        dct = dict()
        dct['ts'] = self.ts
        dct['metadata'] = self.metadata
        dct['dimensions'] = self.dimensions
        return dct

    def impute_values(self):
        """
        ["2011-12-01T00:00:00.000Z",34] or ["2011-12-01T00:00:00.000Z",1,34]
        :param ts:
        :return:
        """
        ts = self.ts
        if self.impute_method == 'previous':
            for i in range(len(ts) - 1):
                this_tup = ts[i]
                next_tup = ts[i + 1]
                if this_tup[len(this_tup) - 1] and not next_tup[len(next_tup) - 1]:
                    next_tup[len(next_tup) - 1] = this_tup[len(this_tup) - 1]

        return self.remove_nulls(ts)

    @staticmethod
    def remove_nulls(ts):
        for tup in ts:
            if not tup[len(tup)-1]:
                ts.remove(tup)
        return ts


    @staticmethod
    def get_sub_tuple(tup):
        return tup[0], tup[len(tup) - 1]

    @staticmethod
    def pct_change(ts):
        """
        This function calculates the percentage for the aggregations calculated by ES
        :param ts: ts as calculated by this class
        :return: ts with values as percentage change
        """
        new_ts = list()
        for i in range(len(ts) - 1):
            j = i + 1
            new_ts.append(TimeSeries.calculate_change_tuples(ts[i], ts[j]))
        return new_ts

    @staticmethod
    def calculate_change_tuples(tup_a, tup_b):
        """

        :param tup_a: tuple with format ["2011-12-01T00:00:00.000Z",34] or ["2011-12-01T00:00:00.000Z",1,34]
        :param tup_b: tuple with format ["2011-12-01T00:00:00.000Z",67] or ["2011-12-01T00:00:00.000Z",2, 67]
        :return: tup_b with updated value as the percentage change
        """
        ret = tup_b[:-1]
        ret.append(TimeSeries.calculate_percent_change(tup_a[len(tup_a) - 1], tup_b[len(tup_b) - 1]))
        return ret

    @staticmethod
    def calculate_percent_change(value_a, value_b):
        """
        This function calculates the percentage change in from value_a to value_b
        :param value_a: valid number
        :param value_b: valid number
        :return: percentage change calculated according to formula: abs((a-b)/a)
        """
        if not value_a or not value_b:
            return None

        if not (isinstance(value_a, numbers.Number) and isinstance(value_b, numbers.Number)):
            message = "Input parameters to the function \"calculate_percentage_change\" should be a valid number, " \
                      "but was instead: {} and {}".format(value_a, value_b)
            raise ValueError(message)

        if value_a == 0:
            raise None
        return abs((float(value_a) - float(value_b)) / float(value_a)) * 100


class DigOutputProcessor():
    DIG_KEY = "key"
    DIG_KEY_AS_STRING = "key_as_string"
    DIG_VALUE = "doc_count"

    SPEC_TYPE = "type"
    SPEC_SEMANTIC_TYPE = "semantic_type"

    def __init__(self, fn, field, date):
        self.ts = self.load(fn)
        self.field = field
        self.date = date

    def make_dig_dimension(self, dtype, spec_type):
        return {self.SPEC_TYPE: dtype, self.SPEC_SEMANTIC_TYPE: spec_type}

    # Processes a dig timeseries output and generates a new version timeseries
    def process(self):
        new_ts = []
        key = self.DIG_KEY_AS_STRING if self.date else self.DIG_KEY
        for ts_item in self.ts:
            if self.field is None:
                new_ts.append([ts_item[key], ts_item[self.DIG_VALUE]])
            else:
                new_ts.append([ts_item[key], ts_item[self.DIG_VALUE], ts_item[self.field]['value']])
        types = []
        types.append(self.make_dig_dimension(type(ts_item[self.DIG_VALUE]).__name__, "count"))
        if self.field is not None:
            types.append(self.make_dig_dimension(type(ts_item[self.field]['value']).__name__, str(self.field)))
        return new_ts, types

    @staticmethod
    def load(dig_output_fn):
        # for now it is a text file. It may change in the future
        json_decoded = dig_output_fn
        return json_decoded['buckets']


import json, codecs

ts_o = json.load(codecs.open('/tmp/timeseries.json'))
print json.dumps(ts_o['ts'])
ts = ts_o['ts']
import requests

timeseries=TimeSeries(ts, None, None)
print json.dumps(timeseries.ts)