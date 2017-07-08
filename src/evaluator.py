from . import utils
from .sequence import Sequence

import operator

class TestPoint:
    def __init__(self, condition_id, data_type, channel, expected_value, check_interval, *,
                 check_function=None, aggregator=None):
        self.condition_id = condition_id
        self.data_type = data_type
        self.channel = channel
        self.expected_value = expected_value
        self.check_interval = check_interval
        self.check_function = check_function
        self.aggregator = aggregator


    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.__dict__ == other.__dict__

    def __str__(self):
        return repr(self)

    def __repr__(self):
        s = "TestPoint: condition_id={}, data_type={}, channel={}, expected_value={}"
        s += ", check_interval={}, check_function={}, aggregator={}"
        return s.format(self.condition_id, self.data_type, self.channel, self.expected_value,
                        self.check_interval, self.check_function, self.aggregator)

    def __lt__(self, other): # Mostly used for test purposes
        t1 = (self.condition_id, hash(type(self.data_type)), self.data_type.value, 
              self.check_interval, hash(self.channel))
        t2 = (other.condition_id, hash(type(other.data_type)), other.data_type.value,
              other.check_interval, hash(other.channel))
        return t1 < t2

class Evaluator:
    # conditions: a list of relevant Conditions
    # test_points: a list of test points
    def __init__(self, conditions, test_points, *,
                 aggregators=None, default_intrapoint_aggregators=None,
                 default_check_functions=None):
        if aggregators is None:
            aggregators = utils.DEFAULT_AGGREGATORS
        if default_intrapoint_aggregators is None:
            default_intrapoint_aggregators = utils.DEFAULT_AGGREGATORS
        if default_check_functions is None:
            default_check_functions = utils.DEFAULT_CHECK_FUNCTIONS


        self.conditions = conditions # List of relevant Conditions
        self.test_points = test_points # List of test_points
        self.aggregators = aggregators # (data_type,channel)->function(list(bool)->bool)

        # Defaults for test_points if respective fields are None
        self.default_intrapoint_aggregators = default_intrapoint_aggregators
        self.default_check_functions = default_check_functions

        for point in test_points: # Populate missing fields with Evalutor's defaults
            if point.aggregator is None:
                point.aggregator = utils.get_default(point.data_type, point.channel,
                                                     default_intrapoint_aggregators)
                if point.aggregator is None: # Error
                    msg = "Evaluator could not resolve aggregator for a test point"
                    raise ValueError(msg)

            if point.check_function is None:
                point.check_function = utils.get_default(point.data_type, point.channel,
                                                         default_check_functions)
                if point.check_function is None: # Error
                    msg = "Evaluator could not resolve check function for a test point"
                    raise ValueError(msg)



    # log: a RequestLog of the test that was run
    # Returns map from (data_type,channel)->bool representing overall result
    def evaluate(self, log):
        satisfied_times = [log.condition_satisfied_at(c) for c in self.conditions]
        sequences = log.extract_sequences()

        results = {} # Map from (data_type,channel) to list(bool) representing relevant results
        for test_point in self.test_points:
            result = self.evaluate_test_point(sequences, satisfied_times, test_point)
            key = (test_point.data_type, test_point.channel)
            if key not in results:
                results[key] = []
            results[key].append(result)

        # Now, for each (data_type, channel), aggregate results to a single bool
        for key in results:
            (data_type, channel) = key
            agg = utils.get_default(data_type, channel, self.aggregators)
            if agg is None:
                results[key] = False # No aggregator of this key or a parent
            else:
                results[key] = agg(results[key])
        return results

    # sequences: Map from (data_type,channel) to Sequence
    # satisfied_times: A list of satisfied times (or None) for conditions
    # test_point: the test_point to evaulate
    # Returns: a bool representing the result for this point
    def evaluate_test_point(self, sequences, satisfied_times, test_point):
        if test_point.condition_id >= len(satisfied_times):
            return False # Condition out of bounds
        else:
            zero_point = satisfied_times[test_point.condition_id]
            if zero_point is None:
                return False # Condition never met, this test point can't be evaluated

        (start, end) = test_point.check_interval
        start += zero_point
        end += zero_point

        # Get relevant actual ouputs
        key = (test_point.data_type, test_point.channel)
        seq = sequences.get(key, Sequence())
        values = seq.get_values(start, end)

        def check(value):
            return test_point.check_function(test_point.expected_value, value)

        return test_point.aggregator(map(check, values))

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        if not (self.conditions == other.conditions
                and self.aggregators == other.aggregators):
            return False

        # Now check that the test_points match
        return sorted(self.test_points) == sorted(other.test_points)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        s = "Evaluator: conditions={}, test_points={}, aggregators={}"
        return s.format(self.conditions, self.test_points, self.aggregators)