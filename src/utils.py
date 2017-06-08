# Later: reorganize this into more logical modules
from enum import Enum

class MessageType(Enum):
    #TODO all of these
    pass

class Request:
    def __init__(self, msg_type, timestamp, body):
        self.msg_type = msg_type
        self.timestamp = timestamp
        self.body = body

    # TODO: a bunch of utility methods

class Response:
    def __init__(self, msg_type, body):
        self.msg_type = msg_type
        self.body = body

    #TODO: a bunch of utility methods

class Frame:
    def __init__(self, inputFrame, outputFrame):
        self.inputFrame = inputFrame
        self.outputFrame = outputFrame

class Test:
    # Collection of Frames, Frame is an inputFrame and outputFrame and accumulation function