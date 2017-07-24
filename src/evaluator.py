from . import prefs
from . import utils
from .sequence import Sequence

from collections import namedtuple
import operator


EvaluatedValue = namedtuple("EvaluatedValue", ["value", "portion", "passed"])
EvaluationPointResult = namedtuple("EvaluationPointResult", ["passed", "observed"])

class EvaluationPoint:
    def __init__(self, condition_id, expected_value, check_interval, *,
                 check_function=operator.eq, portion=1.0):
        self.condition_id = condition_id
        self.expected_value = expected_value
        self.check_interval = check_interval
        self.check_function = check_function
        self.portion = portion # Required fraction of interval with correct value

    # Evaluates whether or not this point is satisfied
    # condition_met_at: time condition was met, or None if not met
    # sequence: Sequence for relevant (data_type,channel)
    # Returns a (bool, list of tuples) tuple:
    #   bool represents whether or not the point is satisfied
    #   each tuple in list is (value_observed, portion_observed, passed),
    #       representing the values observed the assessment interval,
    #       sorted by portion_observed descending
    def evaluate(self, condition_met_at, sequence):
        if condition_met_at is None:
            return EvaluationPointResult(False, [])

        (start, end) = self.check_interval
        start += condition_met_at
        end += condition_met_at

        values = sequence.profile_interval((start,end))

        # Add pass/fail for each value tuple
        portion_correct = 0.0
        for i in range(len(values)):
            value, portion = values[i]
            if self.check_function(self.expected_value, value):
                values[i] = EvaluatedValue(value, portion, True)
                portion_correct += portion
            else:
                values[i] = EvaluatedValue(value, portion, False)

        passed = (portion_correct >= self.portion)
        return EvaluationPointResult(passed, values)

    def __eq__(self, other):
        return type(other) is type(self) and self.__dict__ == other.__dict__

    def __str__(self):
        return repr(self)

    def __repr__(self):
        s = ("EvaluationPoint: condition_id={}, expected_value={}, "
             "check_interval={}, check_function={}, portion={}")
        return s.format(self.condition_id, self.expected_value, self.check_interval,
                        self.check_function, self.portion)

class Evaluator:
    # conditions: a list of relevant Conditions
    # points: a list of EvaluationPoints
    def __init__(self, conditions, points, *,
                 aggregators=None):
        if aggregators is None:
            aggregators = prefs.default_aggregators()

        self.conditions = conditions # List of relevant Conditions
        self.points = points # Map from (data_type,channel)->list(EvaluationPoint)
        self.aggregators = aggregators # Preferences<Aggregator>

    # log: a RequestLog of the test that was run
    # Returns a map from (data_type,channel)->(bool, list)
    #   the boolean represents the overall result for this channel
    #   each elt of list is of EvaluationPointResults corresponding to each
    #   EvaluationPoint (in the same order seen in the values of self.points)
    def evaluate(self, log):
        satisfied_times = [log.condition_satisfied_at(c) for c in self.conditions]
        sequences = log.extract_sequences()
        
        results = {} # Map to be returned
        for key in self.points:
            sequence = sequences.get(key, Sequence())
            point_results = []
            for point in self.points[key]:
                condition_met_at = satisfied_times[point.condition_id]
                point_results.append(point.evaluate(condition_met_at, sequence))

            agg = self.aggregators.get_preference(key)
            overall_result = agg([res.passed for res in point_results])
            results[key] = (overall_result, point_results)

        return results

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return (self.conditions == other.conditions
                and self.aggregators == other.aggregators
                and self.test_points == other.test_points)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        s = "Evaluator: conditions={}, test_points={}, aggregators={}"
        return s.format(self.conditions, self.test_points, self.aggregators)