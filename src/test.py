from request import *
from response import *
from collections import namedtuple

LogEntry = namedtuple('LogEntry', ['request', 'response', 'frame_id']):

class Test:
    # TODO: implement as unique ID Frames
    # TODO: Test class should include check_aggregate() for frames
    
    def __init__(self, end_condition, frames=None):
        self.end_condition = end_condition # Condition for overall test completion
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
                #value = frame.get_value(request.timestamp, request.data_type, request.channel)
                #if frame.analog_params in None:  # Value is digital, pass along unchanged


        else: # Regular ACK for non-inputs
            response = AckResponse()

        self.end_condition.update(request)
        if self.end_condition.is_satisfied():
            response.test_complete = True
        else:
            response.test_complete = False


        #TODO: implement
        pass

    # TODO: description
    def get_current_frame_id(self):
        