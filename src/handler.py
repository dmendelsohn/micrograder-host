from enum import Enum

from . import utils
from .response import AckResponse
from .response import ErrorResponse
from .response import ValuesResponse

class RequestHandler:
    def __init__(self, end_condition, frames, 
                 *, preempt=True, default_values=utils.DEFAULT_VALUES):
        self.end_condition = end_condition # Condition for overall test completion
        self.preempt = preempt # If True, later frame wins in when priority is tied
        self.frames = frames # List of frames
        self.default_values = default_values
        self.clear() # Make sure all state is cleared out

    # Reset the stateful fields
    def clear(self):
        self.end_condition.clear()
        for frame in self.frames:
            frame.clear()

    # Input: Request
    # Return: Response
    def update(self, request):
        for frame in self.frames:
            frame.update(request)

        if not request.is_valid:
            response = ErrorResponse() # InvalidRequest
        elif request.is_input and request.values is None: # Get values from a frame
            frame_id = self.get_current_frame_id()
            if frame_id is None: # No frame currently in progress
                response = ErrorResponse() # Cannot respond to request
            else:
                frame = self.frames[frame_id]
                response = frame.get_response(request)
                if type(response) is ErrorResponse: # Frame couldn't respond, so construct default
                    values = []
                    for i in range(request.batch_params.num):
                        for channel in request.channels:
                            value = utils.get_default_value(request.data_type, channel,
                                                            defaults=self.default_values)
                            values.append(value)

                    if None in values: # Some channel had undefined default
                        response = ErrorResponse()
                    elif request.analog_params is None: # digital values
                        response = ValuesResponse(values=values, analog=False)
                    else: # analog
                        values = [utils.analog_to_digital(v, request.analog_params) for v in values]
                        response = ValuesResponse(values=values, analog=True)
        else:
            response = AckResponse() # Just acknowledge request that doesn't need values

        # Set complete field and return
        self.end_condition.update(request)
        response.complete = self.end_condition.is_satisfied()
        return response

    # Returns the id of the frame that is currently prioritized to serve an input request
    def get_current_frame_id(self):
        actives = [(i, self.frames[i].priority, self.frames[i].start_time) 
                        for i in range(len(self.frames)) if self.frames[i].is_active()]
        if len(actives) == 0:
            return None # No active frames
        highest_priority = max(a[1] for a in actives)
        priority_actives = list(filter(lambda a: a[1]==highest_priority, actives))
        priority_actives.sort(key=lambda a: a[2]) # Sort by start_time
        if self.preempt:
            return priority_actives[-1][0] # Return id of frame with latest start_time
        else:
            return priority_actives[0][0] # Return id of frame with earlest start_time

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return (self.end_condition == other.end_condition
                and self.frames == other.frames
                and self.preempt == other.preempt)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        s = "RequestHandler: frames={}, end_condition={}, preempt={}"
        return s.format(self.frames, self.end_condition, self.preempt)