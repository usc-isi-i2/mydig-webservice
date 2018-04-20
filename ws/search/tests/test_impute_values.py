import unittest
import sys
import json

sys.path.append('../')

from response_converter import TimeSeries


class TestImputeTSValues(unittest.TestCase):
    def setUp(self):
        str_ts1 = """[["2012-08-01T00:00:00.000Z",1,null],["2012-09-01T00:00:00.000Z",1,416.1],
        ["2012-10-01T00:00:00.000Z",1,426.4],["2012-11-01T00:00:00.000Z",1,450],
        ["2012-12-01T00:00:00.000Z",1,472.5],["2013-01-01T00:00:00.000Z",1,121.6],
        ["2013-02-01T00:00:00.000Z",null],["2013-03-01T00:00:00.000Z",1,129.9],
        ["2013-04-01T00:00:00.000Z",1,127.2],["2013-05-01T00:00:00.000Z",1,127],["2013-06-01T00:00:00.000Z",1,122.3],
        ["2013-07-01T00:00:00.000Z",1,119.8],["2013-08-01T00:00:00.000Z",1,119.1], ["2013-09-01T00:00:00.000Z",1,0], 
        ["2013-10-01T00:00:00.000Z",1,23]]"""
        self.ts_obj1 = TimeSeries(json.loads(str_ts1), None, None, impute_method='previous')
        self.ts_obj2 = TimeSeries(json.loads(str_ts1), None, None, impute_method='average')

    def test_impute_values_previous(self):
        ts = self.ts_obj1.ts
        self.assertTrue(len(ts) == 14)
        self.assertEqual(ts[5][len(ts[5]) - 1], 121.6)
        self.assertEqual(ts[12][len(ts[12]) - 1], 0)

    def test_impute_values_average(self):
        ts = self.ts_obj2.ts
        self.assertEqual(len(ts), 12)
        self.assertEqual(ts[5][len(ts[5]) - 1], 125.75)
