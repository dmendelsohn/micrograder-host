from request import *
from response import *
from collections import namedtuple

LogEntry = namedtuple('LogEntry', ['request', 'response', 'frame_id']):

class Test:
    # TODO: implement as unique ID Frames
    # TODO: Test class should include check_aggregate() for frames
    
    def __init__(self, end_condition, frames=None, preempt=True):
        self.end_condition = end_condition # Condition for overall test completion
        self.preempt = preempt # If True, later frame wins in when priority is tied
        if frames:
            self.frames = frames
        else:
            self.frames = []

    def add_frame(self, frame):
        self.frames.append(frame)

    # Return Response, frame_id
    def update(self, request): # request is a well-formed Request
        for frame in self.frames:
            frame.update(request)

        frame_id = self.get_current_frame_id()
        if request.is_input: # pass along request to specific frame
            if frame_id is None: # No frame is currently in progress
                response = ErrorResponse() # Cannot respond to request
            else:
                frame = self.frames[frame_id]
                values = [frame.get_value(timestamp=request.timestamp,
                                        input_type=request.data_type,
                                        channel=channel,
                                        analog_params=request.analog_params)
                            for channel in request.channels]

                analog = (request.analog_params is not None)
                if analog:
                    values = [utils.adc(value, request.analog_params) for value in values]

                response = ValuesResponse(values=values, analog=analog)

        else: # Regular ACK for non-inputs
            response = AckResponse()

        # Determine if end condition is satisfied
        self.end_condition.update(request)
        if self.end_condition.is_satisfied():
            response.test_complete = True
        else:
            response.test_complete = False

        return response

    # TODO: description
    def get_current_frame_id(self):
        actives = [(i, self.frames[i].priority, self.frames[i].start_time) 
                        for i in range(len(self.frames))if self.frames[i].is_active()]
        if len(actives) == 0:
            return None # No active frames
        highest_priority = max(actives, key=lambda x: x[1])
        priority_actives = list(filter(lambda x: x[1]==highest_priority, actives))
        priority_actives.sort(key=lambda x: x[2]) # Sort by start_time
        if self.preempt
            return priority_actives[-1][0] # Return id of frame with latest start_time
        else:
            return priority_actives[0][0] # Return id of frame with earlest start_time
