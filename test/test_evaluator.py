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

    def test_describe(self):
        check_func = lambda x,y: True
        point = EvalPoint(condition_id=0, expected_value=1, check_interval=(0,100),
                          check_function=check_func, portion=0.5)

        point_result = EvalPointResult(True, [
            EvaluatedValue(1, 0.5, True)
        ])
        actual = point.describe("some condition", point_result)
        expected = {
            "Time Interval":"(0, 100) relative to some condition",
            "Pass Criterion":"Correct for 50.00% of interval",
            "Expected Value":1,
            "Result":"PASS",
            "Observed Values":[{
                "Value": 1, "Percentage of Interval": "50.00%", "Correct": "Yes"
                }]
        }
        self.assertEqual(actual, expected)

        point_result = EvalPointResult(False, [])
        actual = point.describe("some condition", point_result)
        expected = {
            "Time Interval":"(0, 100) relative to some condition",
            "Pass Criterion":"Correct for 50.00% of interval",
            "Expected Value":1,
            "Result":"FAIL",
            "Observed Values":[]
        }
        self.assertEqual(actual, expected)

        point.check_function.description = "some check function"
        actual = point.describe()
        expected = {
            "Time Interval":"(0, 100) relative to condition 0",
            "Pass Criterion":"Correct for 50.00% of interval with check function (some check function)",
            "Expected Value":1,
            "Result":"NOT EVALUATED",
            "Observed Values":[]
        }
        self.assertEqual(actual, expected)


class TestEvaluator(unittest.TestCase):
    def setUp(self):
        conditions = [Condition(ConditionType.After, cause=50, description="50ms"),
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

        requests = [
            OutputRequest(timestamp=0, data_type=OutputType.DigitalWrite,
                          channels=[13,14], values=[1,1]),
            EventRequest(timestamp=100, data_type=EventType.Print, data="foo")
        ]
        log = RequestLog()
        for request in requests:
            log.update(request)

        self.log = log

    def test_evaluate(self):
        expected = {}
        expected[(OutputType.DigitalWrite, 13)] = (False, [
            EvalPointResult(True, [EvaluatedValue(value=1, portion=1.0, passed=True)]),
            EvalPointResult(False, [EvaluatedValue(value=1, portion=1.0, passed=False)])
        ])
        expected[(OutputType.DigitalWrite, 15)] = (False, [
            EvalPointResult(False, [])
        ])


        actual = self.evaluator.evaluate(self.log)
        self.assertEqual(actual, expected)

        # This should make (DigitalWrite,13) pass
        self.evaluator.aggregators = Preferences({
            tuple(): all,
            (OutputType.DigitalWrite, 13): any
        })

        overall_result, point_results = expected[(OutputType.DigitalWrite, 13)]
        expected[(OutputType.DigitalWrite, 13)] = (True, point_results) # 1 out 2 points => PASS

        actual = self.evaluator.evaluate(self.log)
        self.assertEqual(actual, expected)

    def test_describe(self):
        self.evaluator.points = {(OutputType.DigitalWrite, 13): [
            EvalPoint(condition_id=0, expected_value=1, check_interval=(0,100))
        ]}

        expected = {(OutputType.DigitalWrite, 13): {
            "Result": "PASS",
            "Points": [{
                "Time Interval": "(0, 100) relative to 50ms",
                "Pass Criterion": "Correct for 100.00% of interval",
                "Expected Value": 1,
                "Result": "PASS",
                "Observed Values": [
                    {"Value":1, "Percentage of Interval":"100.00%", "Correct":"Yes"}
                ]
            }]
        }}
        actual = self.evaluator.describe(self.evaluator.evaluate(self.log))
        self.assertEqual(actual, expected)

        self.evaluator.conditions[0].description = None
        my_agg = lambda values: False
        my_agg.description = "my aggregator"
        self.evaluator.aggregators = Preferences({
            tuple(): my_agg
        })

        expected = {(OutputType.DigitalWrite, 13): {
            "Result": "FAIL",
            "Aggregator Description": "my aggregator",
            "Points": [{
                "Time Interval": "(0, 100) relative to condition 0",
                "Pass Criterion": "Correct for 100.00% of interval",
                "Expected Value": 1,
                "Result": "PASS",
                "Observed Values": [
                    {"Value":1, "Percentage of Interval":"100.00%", "Correct":"Yes"}
                ]
            }]
        }}
        actual = self.evaluator.describe(self.evaluator.evaluate(self.log))
        self.assertEqual(actual, expected)
