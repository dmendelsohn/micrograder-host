import bisect
from enum import enum
from collections import namedtuple

class ConditionType(Enum):
    AFTER = 1
    OR = 2      # or(subconditions)
    AND = 3     # and(subconditions)

class Condition:
    # if cond_type is AFTER, cause is required
    #   subconditions[1:] are ignored
    #   cause is evaluated after subcondition[0].satisfied_at
    #       ... or t=0 if subconditions not given
    # if cond_type is OR or AND, subconditions must be non-empty list of conditions
    def __init__(self, cond_type, cause=None, subconditions=None):
        self.satisfied_at = None  # Initially, condition is automatically unsatisfied (i.e. t=None)
        self.type = cond_type
        self.cause = cause # integer (i.e. time), or function from request -> boolean
        self.subconditions = subconditions
        self.last_update_request = None

    def is_satisfied(self):
        return self.satisfied_at is not None

    def satisfied_at(self):
        return self.satisfied_at

    def update(self, request):
        if self.last_update_request == requst:
            return # No need to do anything, already updated for this request
        self.last_update_request = request

        if self.is_satisfied():
            return # No need to do anything, condition already satisfied

        elif self.type == Condition.AFTER:
            if self.subconditions:
                self.subconditions[0].update()
                start_time = self.subconditions[0].satisfied_at
            else:
                start_time = 0 # No subconditions, so starts at t=0

            if start_time is not None:
                if isinstance(self.cause, int): # satisfy a certain number of millis after start
                    satisfied_time = start_time + self.cause
                    if satisfied_time <= request.timestamp:
                        self.satisfied_at = satisfied_time
                else: # cause is a function from request -> boolean
                    if self.cause(request):
                        self.satisfied_at = request.timestamp

        elif self.type == ConditionType.OR:
            sub_times = []
            for subcondition in subconditions:
                subcondition.update(request)
                sub_times.append(subcondition.satisfied_at)
            
            if any(t is not None for t in sub_times): # If any t != None, we're satisfied
                self.satisfied_at = min(t for t in sub_times if t is not None) # min of non-Nones

        elif self.type == ConditionType.AND:
            sub_times = []
            for subcondition in subconditions:
                subcondition.update(request)
                sub_times.append(subcondition.satisfied_at)
            
             if None not in sub_times: # If all elts in sub_times are not None, we're satisfied
                self.satisfied_at = max(sub_times)

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

class FrameStatus(Enum):
    NotBegun = 1
    InProgress = 2
    Complete = 3
    Avoided = 4

class Frame:
    def __init__(self, start_condition, end_condition, priority=0):
        self.start_condition = start_condition # Should be of type Condition
        self.end_condition = end_condition  # Should be of type Condition
        self.start_time = None
        self.status = FrameStatus.NotBegun
        self.inputs = {} # Build with add_input method
        self.priority = priority

    # input_type is an InputType, sequence is of type ValueSequence
    def add_input(self, sequence, input_type, channel=None):
        self.inputs[(input_type, channel)] = sequence


    # t is an integer (time), input_type an InputType
    # Returns latest value, for this input type, at a time <= t
    # Returns None if no value exists at a time <= t for input_type, or if Frame isn't in progress
    def get_value(self, t, input_type, channel=None):
        if self.status != FrameStatus.InProgress:
            return None  # No value since the frame is not in progress
        key = (input_type, channel)
        if key not in self.sequences:
            return None  # No value for that input_type, channel combo
        relative_t = (t - self.start_time) 
        return self.inputs[key].get_value(relative_t)

    # TODO: description
    def update(self, request):
        self.start_condition.update(request)
        self.start_time = self.start_condition.satisfied_at()
        self.end_condition.update(request)

        is_started = self.start_condition.is_satisfied()
        is_ended = self.end_condition.is_satisfied()
        if is_started and is_ended:
            self.status = FrameStatus.Complete
        elif is_started and not is_ended:
            self.status = FrameStatus.InProgress
        elif not is_started and is_ended:
            self.status = FrameStatus.Avoided # This frame can never be triggered
        elif not is_started and not is_ended:
            self.status = FrameStatus.NotBegun

    def is_active(self):
        return self.status == FrameStatus.InProgress