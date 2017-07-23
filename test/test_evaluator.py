from src.evaluator import *
import unittest

import operator

from src.condition import Condition
from src.condition import ConditionType
from src.log import RequestLog
from src.prefs import Preferences
from src.request import EventRequest
from src.request import OutputRequest
from src.utils import EventType
from src.utils import OutputType

class TestEvaluator(unittest.TestCase):
    def setUp(self):
        conditions = [Condition(ConditionType.After, cause=50),
                      Condition(ConditionType.After, cause=5000)] # Never met
        tp0 = TestPoint(condition_id=0,
                       data_type=OutputType.DigitalWrite,
                       channel=13,
                       expected_value=1,
                       check_interval=(0,100)) # Use some defaults
        tp1 = TestPoint(condition_id=0,
                       data_type=OutputType.DigitalWrite,
                       channel=13,
                       expected_value=0,
                       check_interval=(0,100)) # Use some defaults
        tp2 = TestPoint(condition_id=0,
                       data_type=OutputType.DigitalWrite,
                       channel=14,
                       expected_value=1,
                       check_interval=(0,100),
                       check_function=lambda x,y:True, # Always True
                       aggregator=lambda x: True) # Always True
        tp3 = TestPoint(condition_id=1,
                        data_type=OutputType.DigitalWrite,
                        channel=15,
                        expected_value=1,
                        check_interval=(0,100),
                        check_function=lambda x,y: True, # Always True
                        aggregator=lambda x: True) # Always True
        tp4 = TestPoint(condition_id=2,
                        data_type=OutputType.DigitalWrite,
                        channel=15,
                        expected_value=1,
                        check_interval=(0,100),
                        check_function=lambda x,y: True, # Always True
                        aggregator=lambda x: True) # Always True
        tp5 = TestPoint(condition_id=0,
                        data_type=EventType.Print,
                        channel=None,
                        expected_value="foo",
                        check_interval=(0,100),
                        check_function=operator.eq,
                        aggregator=any)

        test_points = [tp0, tp1, tp2, tp3, tp4, tp5]

        self.evaluator = Evaluator(conditions, test_points)

    #TODO: move to a TestTestPoint class
    def test_describe_point(self):
      tp = self.evaluator.test_points[0]
      expected = {"Type": "Digital pin 13 output", "Expected":"1",
                  "Time Interval": "(0, 100) relative to time at which condition 0 was met"}
      self.assertEqual(tp.describe(), expected)

      expected["Time Interval"] = "(0, 100) relative to foo"
      self.assertEqual(tp.describe(condition_desc="foo"), expected)

      tp.check_function = lambda x,y: tp.check_function(x,y) # Wrap in case it's a built-in
      tp.check_function.description = "bar" # Add a description

      tp.aggregator = lambda args: tp.aggregator(args) # Wrap in case it's a built-in
      tp.aggregator.description = "baz" # Add a description

      expected["Check Function"] = "bar"
      expected["Aggregator Function"] = "baz"
      self.assertEqual(tp.describe(condition_desc="foo"), expected)


    def test_value_error(self):
        conditions = self.evaluator.conditions
        test_points = [
            TestPoint(condition_id=0,
                       data_type=OutputType.DigitalWrite,
                       channel=13,
                       expected_value=1,
                       check_interval=(0,100)) # Use some defaults
        ]

        with self.assertRaises(ValueError):
            evaluator = Evaluator(conditions, test_points,
                                  default_intrapoint_aggregators=Preferences({}))

        with self.assertRaises(ValueError):
            evaluator = Evaluator(conditions, test_points,
                                  default_check_functions=Preferences({}))


    def test_evaluate(self):
        requests = [
            OutputRequest(timestamp=0, data_type=OutputType.DigitalWrite,
                          channels=[13,14], values=[1,1]),
            EventRequest(timestamp=100, data_type=EventType.Print, arg="foo")
        ]
        self.log = RequestLog()
        for request in requests:
            self.log.update(request)

        expected = {
            (OutputType.DigitalWrite, 13): False,
            (OutputType.DigitalWrite, 14): True,
            (OutputType.DigitalWrite, 15): False,
            (EventType.Print, None): True
        }

        with self.assertRaises(ValueError):
            self.evaluator.evaluate(self.log) # Point 4 has invalid condition ID
        del self.evaluator.test_points[4]

        self.assertEqual(self.evaluator.evaluate(self.log), expected)

        self.evaluator.aggregators = Preferences({
            tuple(): all,
            (OutputType.DigitalWrite, 13): any
        })
        expected[(OutputType.DigitalWrite, 13)] = True # 1 out 2 points should be good enough
        self.assertEqual(self.evaluator.evaluate(self.log), expected)

    def test_evaluate_with_description(self):
        requests = [
            OutputRequest(timestamp=0, data_type=OutputType.DigitalWrite,
                          channels=[13,14], values=[1,1]),
            EventRequest(timestamp=100, data_type=EventType.Print, arg="foo")
        ]
        self.log = RequestLog()
        for request in requests:
            self.log.update(request)

        del self.evaluator.test_points[4] # Causes ValueError

        expected_results = {
            (OutputType.DigitalWrite, 13): False,
            (OutputType.DigitalWrite, 14): True,
            (OutputType.DigitalWrite, 15): False,
            (EventType.Print, None): True
        }

        def my_all(args):
            return all(args)
        my_all.description = "all"

        self.evaluator.aggregators = Preferences({
            tuple(): all,
            (EventType.Print,): my_all # With description
        })
        self.evaluator.conditions[0].description = "cond desc 0"

        expected_descriptions = {
            (OutputType.DigitalWrite, 13): {
                "Result":"FAIL",
                "Points":[
                    {
                        "Type": "Digital pin 13 output",
                        "Time Interval":"(0, 100) relative to cond desc 0",
                        "Expected":"1",
                        "Values":["1"],
                        "Result":"PASS"
                    },
                    {
                        "Type": "Digital pin 13 output",
                        "Time Interval":"(0, 100) relative to cond desc 0",
                        "Expected":"0",
                        "Values":["1"],
                        "Result":"FAIL"
                    }
                ]
            },
            (OutputType.DigitalWrite, 14): {
                "Result":"PASS",
                "Points":[
                    {
                        "Type": "Digital pin 14 output",
                        "Time Interval":"(0, 100) relative to cond desc 0",
                        "Expected":"1",
                        "Values":["1"],
                        "Result":"PASS"
                    }
                ]
            },
            (OutputType.DigitalWrite, 15): {
                "Result":"FAIL",
                "Points":[
                    {
                        "Type": "Digital pin 15 output",
                        "Time Interval":"(0, 100) relative to time at which condition 1 was met",
                        "Expected":"1",
                        "Values":[],
                        "Result":"FAIL"
                    }
                ]
            },
            (EventType.Print, None): {
                "Result":"PASS",
                "Points":[
                    {
                        "Type": "Print",
                        "Time Interval":"(0, 100) relative to cond desc 0",
                        "Expected":"foo",
                        "Values":["None","foo"],
                        "Result":"PASS"
                    }
                ],
                "Aggregator Function":"all"
            }
        }

        expected = expected_results, expected_descriptions
        self.assertEqual(self.evaluator.evaluate(self.log, describe=True), expected)

    def test_evaluate_point(self):
        satisfied_times = [50, None]
        sequences = {
            (OutputType.DigitalWrite, 13): Sequence(times=[0], values=[1]),
            (EventType.Print, None): Sequence(times=[100], values=["foo"])
        }

        def evaluate_point(test_point):
          return self.evaluator.evaluate_test_point(sequences, satisfied_times, test_point)
        
        self.assertTrue(evaluate_point(self.evaluator.test_points[0])) # Regular success
        self.assertFalse(evaluate_point(self.evaluator.test_points[1])) # Regular failure
        self.assertTrue(evaluate_point(self.evaluator.test_points[2])) # True, despite no values
        self.assertFalse(evaluate_point(self.evaluator.test_points[3])) # Failure due to unmet condition
        with self.assertRaises(ValueError):
          evaluate_point(self.evaluator.test_points[4]) # Out of bounds condition ID
        self.assertTrue(evaluate_point(self.evaluator.test_points[5])) # Regular success


    def test_evaluate_point_with_description(self):
        satisfied_times = [50, None]
        sequences = {
            (OutputType.DigitalWrite, 13): Sequence(times=[0], values=[1]),
            (EventType.Print, None): Sequence(times=[100], values=["foo"])
        }

        result0 = True
        result_desc0 = self.evaluator.test_points[0].describe()
        result_desc0["Values"] = ["1"]
        result_desc0["Result"] = "PASS"

        result1 = False
        result_desc1 = self.evaluator.test_points[1].describe()
        result_desc1["Values"] = ["1"]
        result_desc1["Result"] = "FAIL"

        expected = [(result0, result_desc0), (result1, result_desc1)]
        actual = [self.evaluator.evaluate_test_point(sequences, satisfied_times, test_point,
                                                     describe=True)
                    for test_point in self.evaluator.test_points[:2]] # Just first two points
        self.assertEqual(actual, expected)

    def test_evaluate_point_defaults(self): # Focus on filling in of default vals
        satisfied_times = [50, None]
        sequences = {
            (OutputType.DigitalWrite, 13): Sequence(times=[0], values=[1]),
            (EventType.Print, None): Sequence(times=[100], values=["foo"])
        }
        conditions = self.evaluator.conditions
        test_points = [
            TestPoint(condition_id=0,
                       data_type=OutputType.DigitalWrite,
                       channel=13,
                       expected_value=1,
                       check_interval=(0,100)), # Use some defaults
            TestPoint(condition_id=0,
                       data_type=OutputType.DigitalWrite,
                       channel=13,
                       expected_value=0,
                       check_interval=(0,100)) # Use some defaults
        ]

        evaluator = Evaluator(conditions, test_points,
                              default_check_functions=Preferences(
                                                        {tuple(): (lambda x,y: False)}
                                                      )
                              )


        actual = evaluator.evaluate_test_point(sequences, satisfied_times, test_points[0])
        self.assertFalse(actual)

        actual = evaluator.evaluate_test_point(sequences, satisfied_times, test_points[1])
        self.assertFalse(actual)

        evaluator = Evaluator(conditions, test_points,
                              default_intrapoint_aggregators=Preferences(
                                                              {tuple(): (lambda vals: False)}
                                                             )
                             )

        actual = evaluator.evaluate_test_point(sequences, satisfied_times, test_points[0])
        self.assertFalse(actual)

        actual = evaluator.evaluate_test_point(sequences, satisfied_times, test_points[1])
        self.assertFalse(actual)


    def test_evalute_point_fine(self): # Focus on exact boundary conditions
        times = [1000]
        key = (OutputType.DigitalWrite, 13)
        tp0 = TestPoint(condition_id=0, data_type=OutputType.DigitalWrite, channel=13,
                       expected_value=1, check_interval=(0,100), check_function=operator.eq,
                       aggregator=all)
        tp1 = TestPoint(condition_id=0, data_type=OutputType.DigitalWrite, channel=13,
                       expected_value=1, check_interval=(0,100), check_function=operator.eq,
                       aggregator=any)

        sequences = {key: Sequence(times=[900, 1000, 1050, 1100], values=[0, 1, 1, 0])}
        self.assertTrue(self.evaluator.evaluate_test_point(sequences, times, tp0))

        # two true points in interval, one false (albeit barely in interval)
        sequences = {key: Sequence(times=[900, 1001, 1050, 1100], values=[0, 1, 1, 0])}
        self.assertFalse(self.evaluator.evaluate_test_point(sequences, times, tp0))
        self.assertTrue(self.evaluator.evaluate_test_point(sequences, times, tp1))


        # sequence becomes false 1 time unit before end of interval
        sequences = {key: Sequence(times=[900, 1000, 1050, 1099], values=[0, 1, 1, 0])}
        self.assertFalse(self.evaluator.evaluate_test_point(sequences, times, tp0))

        # Last value in sequence is in check_interval
        sequences = {key: Sequence(times=[900, 1000, 1050], values=[0, 1, 1])}
        self.assertTrue(self.evaluator.evaluate_test_point(sequences, times, tp0))

        # sequence starts undefined
        sequences = {key: Sequence(times=[1050], values=[1])}
        self.assertFalse(self.evaluator.evaluate_test_point(sequences, times, tp0))
        self.assertTrue(self.evaluator.evaluate_test_point(sequences, times, tp1))

        # sequence always undefined, but key in dictionary
        sequences = {key: Sequence()}
        self.assertFalse(self.evaluator.evaluate_test_point(sequences, times, tp0))
        self.assertFalse(self.evaluator.evaluate_test_point(sequences, times, tp1))

        # key not even in sequences dictionary
        sequences = {}
        self.assertFalse(self.evaluator.evaluate_test_point(sequences, times, tp0))
        self.assertFalse(self.evaluator.evaluate_test_point(sequences, times, tp1))    
