import bisect
from collections import namedtuple
from enum import Enum

TimedValue = namedtuple('TimedValue', ['time', 'value'])

class InterpolationType(Enum):
    START = 0 # Position samples are start of range
    MID = 1 # Position samples in middle of range
    END = 2 # Position samples at end of range
    LINEAR = 3 # Interpolate linearly between samples

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
    def get_sample(self, time):
        index = bisect.bisect(self.times, time+0.1) # +0.1 to break ties
        index -= 1
        if index < 0:
            return None # No inputs before time t
        else:
            return self.values[index]

    def get_samples(self, start_time, num_samples, period): #TODO: make this legit
        index = bisect.bisect(self.times, start_time)
        index -= 1
        if index < 0:
            return None # No inputs before start_time
        
        samples = []
        t = start_time
        for i in range(num_samples):
            samples.append(self.values[index])
            t += period
            while (index+1) < len(self.times) and self.times[index+1] <= t:
                index += 1  # Increment index as far as needed
        return samples

    # Returns list of values in time range [start, end), or [] if no such values exist
    def get_values(self, start_time, end_time):
        index = bisect.bisect(self.times, start_time)
        index -= 1
        results = []
        if index < 0:
            results.append(None) # Initial value is undefiend
            index = 0

        while index < len(self.times) and self.times[index] < end_time:
            results.append(self.values[index])
            index += 1
        return results

    # Returns a subsequence consisting of elements with time in [start, end)
    def get_subsequence(self, start_time, end_time):
        start_index = bisect.bisect(self.times, start_time-0.1) # -0.1 to include exact start
        end_index = bisect.bisect(self.times, end_time-0.1) # -0.1 to exluce exact end
        return Sequence(times=self.times[start_index:end_index],
                        values=self.values[start_index:end_index])

    # Inserta a point into the sequence, returns self
    def insert(self, time, value):
        index = bisect.bisect(self.times, time)
        self.times.insert(index, time)
        self.values.insert(index, value)
        return self

    # Shifts this sequence, returns self
    def shift(self, time_shift):
        self.times = [(t+time_shift) for t in self.times]
        return self

    # Removes duplicates, returns itself
    # A duplicate is a point where the value is the same as the previous point's value
    def remove_duplicates(self):
        if len(self) < 1:
            return Sequence()
        last_value = self.values[0]
        times = [self.times[0]]
        values = [self.values[0]]
        for i in range(1,len(self)):
            if self.values[i] != last_value:
                times.append(self.times[i])
                values.append(self.values[i])
            last_value = self.values[i]
        self.times = times
        self.values = values
        return self

    # Returns a new Sequence that is an interpolated version of self
    def interpolation(self, interpolation_type):
        #TODO: implement
        return self.copy()

    def copy(self):
        return Sequence(times=self.times[:], values=self.values[:])

    def __getitem__(self, key):  # To allow for list-style access
        # TODO: handle slices correctly
        return TimedValue(time=self.times[key], value=self.values[key])

    def __len__(self):
        return len(self.times)  # Should be same as len(self.values)

    def __eq__(self, other):
        return self.times == other.times and self.values == other.values

    def __repr__(self):
        return "Sequence: times={}, values={}".format(self.times, self.values)