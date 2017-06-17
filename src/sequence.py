TimedValue = namedtuple('TimedValue', ['time', 'value']) # times must be non-negative integers
class ValueSequence:
    # values must be list of TimedValue with unique times
    def __init__(self, values=None):
        if values:
            self.values = sorted(values, key=lambda timed_val: timed_val.time)
        else:
            self.values = []

    def append(self, time, value):
        self.values.append(TimedValue(time=time, value=value))

    # Returns latest value with .time <= time, or None if no value exists with .time <= time
    def get_value(time):
        index = bisect.bisect(self.values, (time+0.5, 0)) # +0.5 to break ties
        index -= 1
        if index < 0:
            return None # No inputs before time t
        else:
            return self.values[index].value

    # Returns list of values in time range [start, end), or [] if no such values exist
    def get_values(start, end):
        index = bisect.bisect(self.values, (time+0.5, 0)) # +0.5 to break ties
        index -= 1
        if index < 0:
            return []
        else:
            results = []
            while index < len(self.valeus) and self.values[index].time < end:
                results.append(self.values[index].value)
            return results

    def __getitem__(self, key):  # To allow for list-style access
        return self.values[key]

    def __len__(self):
        return len(self.values)