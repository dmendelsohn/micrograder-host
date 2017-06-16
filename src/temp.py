# All times must be unique non-negative integers
# Check function takes in two values (this, other) and returns a boolean.
# Check interval must be 2-tuple of relative times
ExpectedValue = namedtuple('ExpectedValue',
        ['value', 'check_function', 'check_interval'])

# expected is a dict mapping (OutputType,channel) -> list(ExpectedValue)
# aggregators is dict mapping (OutputType,channel)-> func(list(bool)->bool)
# log is of type TestLog
# zero_time is timestamp that will be considered t=0, when considering relative times
# Returns dict mapping (OutputType,channel) -> boolean (representing passing sequence result)
def assess_frame(expected, aggregators, log, zero_time):
    results = {}
    for (data_type, channel) in expected:
        expected_seq = expected[(data_type, channel)]
        aggregator = aggregators[(data_type, channel)]
        if zero_time is not None: #  Frame actually happened
            actual_sequence = log.get_output_sequence(data_type, channel, zero_time)
            results[(data_type, channel)] = assess_sequence(expected_seq, actual_sequence, aggregator)
        else:
            results[(data_type, channel)] = False
    return results

 # expected is a list of ExpectedValue
 # actual is a ValueSequence
 # aggregator function takes in list of booleans (for each expected), returns boolean
 # Returns output of aggregator
def assess_sequence(expected, actual, aggregator):
    results = (assess_expected_value(exp, actual) for exp in expected)
    return aggregator(results)

#  expected is an ExpectedValue
#  actual is a ValueSequence
#  Returns True if expected value is satisfied for entire check_interval
def assess_expected_value(expected, actual):
    start, end = expected.check_interval
    actual_values = actual.get_values(start, end)
    if actual_values:
        # Check that each of the actual values are a match
        for actual_value in actual_values:
            if not expected.check_function(expected.value, actual_value):
                return False
        return True
    else: # Empty list doesn't count as satisfying criteria
        return False

            # TODO: description
    # Frame id field of LogEntries is ignored, we assume log entry belongs to this frame
    # Returns dictionary mapping (OutputType,channel) to boolean (representing passing test)
#    def assess(self, log):
        #TODO: for each (OutputType,channel), filter, and call OutputSequence evaluate
        #TODO: also, apply dac if necessary
#        pass
