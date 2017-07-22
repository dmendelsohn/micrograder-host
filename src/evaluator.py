from . import utils
from .sequence import Sequence

import operator

class TestPoint:
    def __init__(self, condition_id, data_type, channel, expected_value, check_interval, *,
                 check_function=None, aggregator=None,
                 check_function_desc=None, aggregator_desc=None):
        self.condition_id = condition_id
        self.data_type = data_type
        self.channel = channel
        self.expected_value = expected_value
        self.check_interval = check_interval
        self.check_function = check_function # Can be func or (func, str) tuple
        self.aggregator = aggregator # Can be func or (func, str) tuple

    def describe(self, condition_desc=None):
        json = {}
        json["Type"] = utils.get_description(data_type=self.data_type, 
                                                    channel=self.channel)

        interval_desc = str(self.check_interval) + " relative to "
        if condition_desc is not None:
            interval_desc += condition_desc
        else:
            interval_desc += "time at which condition {} was met".format(self.condition_id)
        json["Time Interval"] = interval_desc

        json["Expected"] = str(self.expected_value)

        if type(self.check_function) is tuple and len(self.check_function) >= 2:
            json["Check Function"] = self.check_function[1]

        if type(self.aggregator) is tuple and len(self.aggregator) >= 2:
            json["Aggregator Function"] = self.aggregator[1]

        return json


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
                 aggregators=None,
                 default_intrapoint_aggregators=None,
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
    def evaluate(self, log, *, describe=False):
        satisfied_times = [log.condition_satisfied_at(c) for c in self.conditions]
        condition_descs = [c.description for c in self.conditions]
        sequences = log.extract_sequences()

        results = {} # Map from (data_type,channel) to list of boolean results
        descriptions = {} # Map from (data_type,channel) to list of description dicts
        for test_point in self.test_points:
            result = self.evaluate_test_point(sequences, satisfied_times, test_point,
                                              describe=describe,
                                              condition_descriptions=condition_descs)

            if describe: # Split off description
                result, desc = result

            key = (test_point.data_type, test_point.channel)
            if key not in results:
                results[key] = []
            results[key].append(result)

            if describe: # Add description to the dictrionary in the same way
                if key not in descriptions:
                    descriptions[key] = []
                descriptions[key].append(desc)


        # Now, for each (data_type, channel), aggregate results to a single bool
        for key in results:
            (data_type, channel) = key
            agg = utils.get_default(data_type, channel, self.aggregators)
            if agg is None:
                results[key] = False # No aggregator of this key or a parent
            else:
                if type(agg) is tuple:
                    results[key] = agg[0](results[key])
                else:
                    results[key] = agg(results[key])

            if describe:
                descriptions[key] = {"Points": descriptions[key]}
                if results[key]:
                    descriptions[key]["Result"] = "PASS"
                else:
                    descriptions[key]["Result"] = "FAIL"
                if type(agg) is tuple:
                    descriptions[key]["Aggregator Function"] = agg[1]

        if describe:
            return results, descriptions
        else:
            return results

    # sequences: Map from (data_type,channel) to Sequence
    # satisfied_times: A list of satisfied times (or None) for all conditions
    # condition_descriptions: A list of strings (or None) for describing conditions.
    #    - optional...if provided, must be same length as conditions list
    # test_point: the test_point to evaulate
    # Returns: a bool representing the result for this point, or a (bool, description) tuple
    #       description is a dict where keys are str and values are (str or list or dict)
    def evaluate_test_point(self, sequences, satisfied_times, test_point, *,
                            describe=False, condition_descriptions=None):
        if condition_descriptions is None:
            condition_descriptions = [None]*len(satisfied_times)

        if test_point.condition_id >= len(satisfied_times): # Condition out of bounds
            raise ValueError("Condition id out of bounds")
        
        zero_point = satisfied_times[test_point.condition_id]
        if zero_point is None: # Condition never met, this point can't be evaluated
            values = []
            result = False
        else:
            (start, end) = test_point.check_interval
            start += zero_point
            end += zero_point

            # Get relevant actual ouputs
            key = (test_point.data_type, test_point.channel)
            seq = sequences.get(key, Sequence())
            values = seq.get_values(start, end)

            def check(value):
                if type(test_point.check_function) is tuple:
                    f = test_point.check_function[0]
                else:
                    f = test_point.check_function
                return f(test_point.expected_value, value)

            if type(test_point.aggregator) is tuple:
                agg = test_point.aggregator[0]
            else:
                agg = test_point.aggregator
            result = agg(map(check, values))

        # Formulate output and return
        if describe:
            condition_desc = condition_descriptions[test_point.condition_id]
            point_desc = test_point.describe(condition_desc=condition_desc)
            point_desc["Values"] = [str(value) for value in values]
            if result:
                point_desc["Result"] = "PASS"
            else:
                point_desc["Result"] = "FAIL"
            return (result, point_desc)
        else:
            return result

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