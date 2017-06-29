from enum import Enum

from . import utils
from .response import ErrorResponse
from .response import ValuesResponse

class FrameStatus(Enum):
    NotBegun = 1
    InProgress = 2
    Complete = 3
    Avoided = 4

class Frame:
    def __init__(self, start_condition, end_condition, inputs={}, priority=0):
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