import unittest
import sys
import json

sys.path.append('../')

from response_converter import TimeSeries


class TestPercentChangeTSValues(unittest.TestCase):

    def test_percent_change_1(self):
        ts1 = [['a', 0.5], ['b', 0.25], ['c', 1], ['d', 5], ['e', 4.75]]
        ts_obj1 = TimeSeries(ts1, None, None, percent_change=True)
        ts = ts_obj1.ts
        expected_ts = [["b", -50.0], ["c", 300.0], ["d", 400.0], ["e", -5.0]]
        self.assertTrue(len(ts) == 4)
        for i in range(len(ts)):
            self.assertEqual(ts[i][len(ts[i]) - 1], expected_ts[i][len(expected_ts[i]) - 1])

    def test_percent_change_2(self):
        ts1 = [['a', 0.5], ['b', 0.25], ['c', 1], ['d', None], ['e', 4.75]]
        ts_obj1 = TimeSeries(ts1, None, None, percent_change=True)
        ts = ts_obj1.ts
        expected_ts = [["b", -50.0], ["c", 300.0], ["d", 0.0], ["e", 375.0]]
        self.assertTrue(len(ts) == 4)
        for i in range(len(ts)):
            self.assertEqual(ts[i][len(ts[i]) - 1], expected_ts[i][len(expected_ts[i]) - 1])

    def test_percent_change_3(self):
        ts1 = [['a', 0.5], ['b', 0.25], ['c', 1], ['d', None], ['e', 4.75]]
        ts_obj1 = TimeSeries(ts1, None, None, percent_change=True, impute_method='average')
        ts = ts_obj1.ts
        print ts
        expected_ts = [["b", -50.0], ["c", 300.0], ["d", 187.5], ["e", 65.21739130434783]]
        self.assertTrue(len(ts) == 4)
        for i in range(len(ts)):
            self.assertEqual(ts[i][len(ts[i]) - 1], expected_ts[i][len(expected_ts[i]) - 1])
