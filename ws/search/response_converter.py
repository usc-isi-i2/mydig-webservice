import json
import sys
import logging
import requests


class TimeSeries(object):
    def __init__(self, ts, metadata, dimensions):
        self.ts = ts
        self.metadata = metadata
        self.dimensions = dimensions

    def to_dict(self):
        dct = {}
        dct['ts'] = self.ts
        dct['metadata'] = self.metadata
        dct['dimensions'] = self.dimensions
        return dct


class DigOutputProcessor():
    DIG_KEY = "key"
    DIG_KEY_AS_STRING = "key_as_string"
    DIG_VALUE = "doc_count"

    SPEC_TYPE = "type"
    SPEC_SEMANTIC_TYPE = "semantic_type"

    def __init__(self, fn,field,date):
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
                new_ts.append([ts_item[key], ts_item[self.DIG_VALUE],ts_item[self.field]['value']])
        types = []
        types.append(self.make_dig_dimension(type(ts_item[self.DIG_VALUE]).__name__, "count"))
        if self.field is not None:
            types.append(self.make_dig_dimension(type(ts_item[self.field]['value']).__name__,str(self.field)))
        return new_ts, types

    @staticmethod
    def load(dig_output_fn):
        # for now it is a text file. It may change in the future
        json_decoded = dig_output_fn
        return json_decoded['buckets']
