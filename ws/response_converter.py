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


class MetaDataProcessor():
    def __init__(self, hfcid):
        self.question_details = self.request_metadata(hfcid)['data']['question']

    @staticmethod
    def request_metadata(hfcid):
        headers = {'content-type': 'application/graphql'}
        payload = """
            {
              question(id: "%d") {
                title,
                createdAt,
                startingAt,
                endingAt,
                description,
                possibilities {  
                    name
                },
                hfcId
              }
            }"""
        r = requests.post('http://sage-test.isi.edu/api/ql', data=payload % hfcid, headers=headers)
        rjson = r.text
        return json.loads(rjson)

    def create_metadata_dict(self, changed_keys=None, excluded_keys=None, new_values=None):
        if changed_keys is not None:
            for old_key, new_key in changed_keys.items():
                self.question_details[new_key] = self.question_details.pop(old_key)

        if excluded_keys is not None:
            for key in excluded_keys:
                self.question_details.pop(key, None)

        if new_values is not None:
            for key, value in new_values.items():
                self.question_details[key] = value

        return self.question_details


class DigOutputProcessor():
    DIG_KEY = "key"
    DIG_KEY_AS_STRING = "key_as_string"
    DIG_VALUE = "doc_count"

    SPEC_TYPE = "type"
    SPEC_SEMANTIC_TYPE = "semantic_type"

    def __init__(self, fn):
        self.ts = self.load(fn)

    def make_dig_dimension(self, dtype, spec_type):
        return {self.SPEC_TYPE: dtype, self.SPEC_SEMANTIC_TYPE: spec_type}

    # Processes a dig timeseries output and generates a new version timeseries
    def process(self):
        new_ts = []
        for ts_item in self.ts:
            new_ts.append([ts_item[self.DIG_KEY_AS_STRING], ts_item[self.DIG_VALUE]])
        return new_ts, self.make_dig_dimension(type(ts_item[self.DIG_VALUE]).__name__, "")

    @staticmethod
    def load(dig_output_fn):
        # for now it is a text file. It may change in the future
        json_decoded = dig_output_fn
        return json_decoded['buckets']


def write_to_file(output_fn, output):
    with open(output_fn, 'w') as outfile:
        print output
        outfile.write(json.dumps(output))
    outfile.close()


def main():
    new_ts, ts_dimension = DigOutputProcessor(sys.argv[1]).process()
    metadata = MetaDataProcessor(hfcid=50).create_metadata_dict({"possibilities": "options"}, {"description"}, {"aggregation_type": "year"})
    ts_obj = TimeSeries(new_ts, metadata, ts_dimension).to_dict()
    write_to_file(sys.argv[2], ts_obj)
    MetaDataProcessor.request_metadata(50)


if __name__ == "__main__":
    main()