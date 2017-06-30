from .sequence import Sequence

class TestPoint:
    def __init__(self, condition_id, data_type, channel, expected_value,
                 check_interval, check_function, aggregator):
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

    def __lt__(self, other):
        t1 = (self.condition_id, hash(type(self.data_type)), self.data_type.value, 
              self.check_interval, hash(self.channel))
        t2 = (other.condition_id, hash(type(other.data_type)), other.data_type.value,
              other.check_interval, hash(other.channel))
        return t1 < t2

class Evaluator:
    # conditions: a list of relevant Conditions
    # test_points: a list of test points
    def __init__(self, conditions, test_points, aggregators):
        self.conditions = conditions # List of relevant Conditions
        self.test_points = test_points # List of test_points
        self.aggregators = aggregators # (data_type,channel)->function(list(bool)->bool) 

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
            if key in self.aggregators:
                agg = self.aggregators[key]
                results[key] = agg(results[key])
            else: # No aggregator for this (data_type, channel)
                results[key] = False
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