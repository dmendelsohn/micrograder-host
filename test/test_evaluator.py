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


class TestEvalPoint(unittest.TestCase):
    def test_evaluate(self):
        seq = Sequence(times=[100, 300], values=[1.00, 1.01])
        point = EvalPoint(condition_id=0, expected_value=1.00, check_interval=(0,400))

        # Test bhavior when condition_met_at is None
        expected = EvalPointResult(False, [])
        self.assertEqual(point.evaluate(None, seq), expected)

        expected = EvalPointResult(False, [
            EvaluatedValue(value=1.00, portion=0.50, passed=True),
            EvaluatedValue(value=1.01, portion=0.25, passed=False)    
        ])
        self.assertEqual(point.evaluate(0, seq), expected)

        # Test if point will pass when portion requirement is lowered just enough
        point.portion = 0.50
        expected = EvalPointResult(True, expected.observed)
        self.assertEqual(point.evaluate(0, seq), expected)

        # Test alternate check functions work
        point.portion = 0.75
        point.check_function = lambda x,y: abs(x-y) < 0.1
        expected = EvalPointResult(True, [
            EvaluatedValue(value=1.00, portion=0.50, passed=True),
            EvaluatedValue(value=1.01, portion=0.25, passed=True)    
        ])

class TestEvaluator(unittest.TestCase):
    def setUp(self):
        conditions = [Condition(ConditionType.After, cause=50),
                      Condition(ConditionType.After, cause=5000)] # Never met

        points = {}
        # For basic tests of passing/failing point, and different aggregations
        points[(OutputType.DigitalWrite, 13)] = [
            EvalPoint(condition_id=0, expected_value=1, check_interval=(0,100)),
            EvalPoint(condition_id=0, expected_value=0, check_interval=(0,100)),
        ]
        # To test that we successfully identify points with unmet conditions
        points[(OutputType.DigitalWrite, 15)] = [
            EvalPoint(condition_id=1, expected_value=1, check_interval=(0,100),
                            check_function=lambda x,y:True, portion=0.0)
        ]

        self.evaluator = Evaluator(conditions, points)

    def test_evaluate(self):
        requests = [
            OutputRequest(timestamp=0, data_type=OutputType.DigitalWrite,
                          channels=[13,14], values=[1,1]),
            EventRequest(timestamp=100, data_type=EventType.Print, data="foo")
        ]
        log = RequestLog()
        for request in requests:
            log.update(request)

        expected = {}
        expected[(OutputType.DigitalWrite, 13)] = (False, [
            EvalPointResult(True, [EvaluatedValue(value=1, portion=1.0, passed=True)]),
            EvalPointResult(False, [EvaluatedValue(value=1, portion=1.0, passed=False)])
        ])
        expected[(OutputType.DigitalWrite, 15)] = (False, [
            EvalPointResult(False, [])
        ])


        actual = self.evaluator.evaluate(log)
        self.assertEqual(actual, expected)

        return
        # This should make (DigitalWrite,13) pass
        self.evaluator.aggregators = Preferences({
            tuple(): all,
            (OutputType.DigitalWrite, 13): any
        })

        overall_result, point_results = expected[(OutputType.DigitalWrite, 13)]
        expected[(OutputType.DigitalWrite, 13)] = (True, point_results) # 1 out 2 points => PASS

        actual = self.evaluator.evaluate(log)
        self.assertEqual(actual, expected)