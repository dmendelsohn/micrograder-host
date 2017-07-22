from src.evaluator import *
import unittest

import operator

from src.condition import Condition
from src.condition import ConditionType
from src.log import RequestLog
from src.request import EventRequest
from src.request import OutputRequest
from src.utils import EventType
from src.utils import OutputType

class TestEvaluator(unittest.TestCase):
    def setUp(self):
        conditions = [Condition(ConditionType.After, cause=50),
                      Condition(ConditionType.After, cause=5000)]
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

    def test_describe_point(self):
      tp = self.evaluator.test_points[0]
      expected = {"Output Type": "Digital pin 13", "Expected":"1",
                  "Time Interval": "(0, 100) relative to time at which condition 0 was met"}
      self.assertEqual(tp.describe(), expected)

      expected["Time Interval"] = "(0, 100) relative to foo"
      self.assertEqual(tp.describe(condition_desc="foo"), expected)

      tp.check_function = (tp.check_function, "bar") # Add a description
      tp.aggregator = (tp.aggregator, "baz") # Add a description
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
                                  default_intrapoint_aggregators={})

        with self.assertRaises(ValueError):
            evaluator = Evaluator(conditions, test_points,
                                  default_check_functions={})


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
        self.assertEqual(self.evaluator.evaluate(self.log), expected)

        self.evaluator.aggregators = {
            None: all,
            (OutputType.DigitalWrite, 13): any
        }
        expected[(OutputType.DigitalWrite, 13)] = True # 1 out 2 points should be good enough
        self.assertEqual(self.evaluator.evaluate(self.log), expected)

    def test_evaluate_point(self):
        satisfied_times = [50, None]
        sequences = {
            (OutputType.DigitalWrite, 13): Sequence(times=[0], values=[1]),
            (EventType.Print, None): Sequence(times=[100], values=["foo"])
        }

        expected = [
            True, # Regular success
            False, # Regular failure
            True, # Always True, despite not even being in sequences
            False, # Failure due to unmet condition
            False, # Failure due to out of bounds condition ID
            True # Regular success
        ]
        actual = [self.evaluator.evaluate_test_point(sequences, satisfied_times, test_point)
                    for test_point in self.evaluator.test_points]
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
                              default_check_functions={None: (lambda x,y: False)})


        actual = evaluator.evaluate_test_point(sequences, satisfied_times, test_points[0])
        self.assertFalse(actual)

        actual = evaluator.evaluate_test_point(sequences, satisfied_times, test_points[1])
        self.assertFalse(actual)

        evaluator = Evaluator(conditions, test_points,
                              default_intrapoint_aggregators={None: (lambda vals: False)})

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
