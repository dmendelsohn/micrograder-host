import bisect
from enum import enum

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
        #TODO: implement
        self.satisfied_at = None  # Initially, condition is automatically unsatisfied (i.e. t=None)
        self.type = cond_type
        self.cause = cause # integer (i.e. time), or function from request -> boolean
        self.subconditions = subconditions
        self.last_update_request = None

    def is_satisfied(self):
        return self.satisfied_at is not None

    def satisfied_at(self):
        return self.satisfied_at

    def update(self, request): #TODO: finish this
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
                    if satisfied_time <= request.get_time():
                        self.satisfied_at = satisfied_time
                else: # cause is a function from request -> boolean
                    if self.cause(request):
                        self.satisfied_at = request.get_time()

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

class InputSequence:
    # values must be sorted list of tuples of form (time, value)
    # All times must be unique non-negative integers
    # All values must be numeric
    def __init__(self, values):  # Later: build more useful constructors / factory functions
        self.values = values

    # Returns latest value at a time <= t, or None if no value exists at a time <= t
    def get_value(t):
        index = bisect.bisect(self.values, (t+0.5, 0)) # +0.5 to break ties
        if index == 0:
            return None # No inputs before time t
        else:
            return self.values[index-1][1]

class OutputSequence:
    #TODO: implement
    pass

class FrameStatus(Enum):
    NOT_BEGUN = 1
    IN_PROGRESS = 2
    COMPLETE = 3
    AVOIDED = 4

class Frame:
    def __init__(self, start_condition, end_condition, priority=0):
        self.start_condition = start_condition # Should be of type 'Event'
        self.end_condition = end_condition  # Should be of type 'Event'
        self.start_time = None
        self.status = FrameStatus.NOT_BEGUN
        self.inputs = {} # Build with add_input method
        self.expected_outputs = {} # Build with add_expected_output method
        self.observed_outputs = {}
        self.priority = priority

    # input_type is InputType (an enum), sequence is of type InputSequence
    def add_input(self, input_type, sequence):
        self.inputs[input_type] = sequence

    # output_type is OutputType (an enum), sequence if of type OutputSequence
    def add_expected_output(self, output_type, sequence):
        #TODO: implement
        pass

    # t is an integer (time), input_type is of type InputType (an enum)
    # Returns latest value at a time <= t
    # Returns None if no value exists at a time <= t for input_type, or if Frame isn't in progress
    def get_value(t, input_type):
        if input_type not in self.sequences:
            return None  # No value for that input_type
        if self.status != FrameStatus.IN_PROGRESS:
            return None  # No value since the frame is not in progress
        relative_t = (t - self.start_time) 
        return self.inputs[input_type].get_value(relative_t)

    # TODO: description
    def update(self, request):
        self.start_condition.update(request)
        self.start_time = self.start_condition.satisfied_at()
        self.end_condition.update(request)

        is_started = self.start_condition.is_satisfied()
        is_ended = self.end_condition.is_satisfied()
        if is_started and is_ended:
            self.status = FrameStatus.COMPLETE
        elif is_started and not is_ended:
            self.status = FrameStatus.IN_PROGRESS
        elif not is_started and is_ended:
            self.status = FrameStatus.AVOIDED # This frame can never be triggered
        elif not is_started and not is_ended:
            self.status = FrameStatus.NOT_BEGUN

        #TODO: if request is a relevant output, log in self.observed_ouputs

    #TODO: evaluate if frame passes test or not
    def evaluate(self):
        #TODO: implement
        pass
        
