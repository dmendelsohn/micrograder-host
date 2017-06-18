import bisect

class Sequence:
    # times must be list of unique increasing integers
    # values is times associated with those times
    def __init__(self, times=None, values=None):
        if values:
            self.times = times
            self.values = values
        else:
            self.times = []
            self.values = []

    # No sorting, we assume caller only calls this with increasing times
    def append(self, time, value):
        self.times.append(time)
        self.values.append(value)

    # Returns latest value with .time <= time, or None if no value exists with .time <= time
    def get_value(self, time):
        index = bisect.bisect(self.times, time+0.1) # +0.1 to break ties
        index -= 1
        if index < 0:
            return None # No inputs before time t
        else:
            return self.values[index]

    # Returns list of values in time range [start, end), or [] if no such values exist
    def get_values(self, start_time, end_time):
        index = bisect.bisect(self.times, start_time+0.1) # +0.1 to break ties
        index -= 1
        results = []
        if index < 0:
            results.append(None) # Initial value is undefiend
            index = 0

        while index < len(self.times) and self.times[index] < end_time:
            results.append(self.values[index])
            index += 1
        return results

    def __getitem__(self, key):  # To allow for list-style access
        return (self.times[key], self.values[key])

    def __len__(self):
        return len(self.times)  # Should be same as len(self.values)