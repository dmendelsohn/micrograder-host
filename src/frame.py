from enum import Enum

from . import utils
from .response import ErrorResponse
from .response import ValuesResponse

class ConditionType(Enum):
    After = 1   # after(t=0) or after(condition)
    Or = 2      # or(subconditions)
    And = 3     # and(subconditions)

class Condition:
    # if cond_type is AFTER, cause is required
    #   subconditions[1:] are ignored
    #   cause is evaluated after subcondition[0].satisfied_at
    #       ... or t=0 if subconditions not given
    # if cond_type is Or or And, subconditions must be non-empty list of conditions, cause is ignored
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

    # request: of type Request
    # returns None
    # updates satisfied_at given the incoming request, and updates child conditions if necessary
    def update(self, request):
        if self.last_update_request == request:
            return # No need to do anything, already updated for this request
        self.last_update_request = request

        if self.is_satisfied():
            return # No need to do anything, condition already satisfied

        elif self.type == ConditionType.After:
            if self.subconditions: # Ensure it's a non-empty list
                self.subconditions[0].update(request)
                start_time = self.subconditions[0].satisfied_at
            else:
                start_time = 0 # No subconditions, so subcondition satisfied at t=0

            if start_time is not None:
                if isinstance(self.cause, int): # satisfy a certain number of millis after start
                    satisfied_time = start_time + self.cause
                    if satisfied_time <= request.timestamp:
                        self.satisfied_at = satisfied_time
                else: # cause is a function from request -> boolean
                    if self.cause(request):
                        self.satisfied_at = request.timestamp

        elif self.type == ConditionType.Or:
            sub_times = []
            for subcondition in self.subconditions:
                subcondition.update(request)
                sub_times.append(subcondition.satisfied_at)
            
            if any(t is not None for t in sub_times): # If any t != None, we're satisfied
                self.satisfied_at = min(t for t in sub_times if t is not None) # min of non-Nones

        elif self.type == ConditionType.And:
            sub_times = []
            for subcondition in self.subconditions:
                subcondition.update(request)
                sub_times.append(subcondition.satisfied_at)
            
            if None not in sub_times: # If all elts in sub_times are not None, we're satisfied
                self.satisfied_at = max(sub_times)

class FrameStatus(Enum):
    NotBegun = 1
    InProgress = 2
    Complete = 3
    Avoided = 4

class Frame:
    def __init__(self, start_condition, end_condition, inputs, priority=0):
        self.start_condition = start_condition # Should be of type Condition
        self.end_condition = end_condition  # Should be of type Condition
        self.start_time = None
        self.status = FrameStatus.NotBegun
        self.inputs = inputs # Should be dict mapping (InputType,channel)->ValueSequence
        self.priority = priority # Should be an integer


    # request is an InputRequest
    # returns ValueResponse for these (input type,channel) with latests values 
    # returns ErrorResponse if no value exists at <= t for any channel, or frame not InProgress
    def get_response(self, request):
        if self.status != FrameStatus.InProgress:
            return ErrorResponse()  # No value since the frame is not in progress

        relative_time = (request.timestamp - self.start_time)
        num_samples, period = request.batch_params.num, request.batch_params.period
        values = [] # List of results for each channel, each result is a list of samples
        for channel in request.channels:
            key = (request.data_type, channel)
            if key not in self.inputs:
                samples = None  # No value for that input_type, channel combo
            else:
                samples = self.inputs[key].get_samples(relative_time, num_samples, period)
            values.append(samples)
        
        if None in values:  # There was an error
            return ErrorResponse()
        else:
            values = [[values[i][n] for i in range(len(request.channels))] 
                                        for n in range(num_samples)] # Transpose 2D array
            values = sum(values, []) # Then flatten into a 1D array of values

        if request.analog_params is None: # digital
            return ValuesResponse(values=values, analog=False)
        else: # analog
            values = [utils.analog_to_digital(v, request.analog_params) for v in values]
            return ValuesResponse(values=values, analog=True)

    # request: of type request
    # returns None
    # given incoming requests, updates start_condition, end_condition, start_time, and status
    def update(self, request):
        self.start_condition.update(request)
        self.start_time = self.start_condition.satisfied_at
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