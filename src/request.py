from enum import Enum
from collections import namedtuple

THREE_AXIS = ['x', 'y', 'z']  # Standard channels for three axis quantities

class InputType(Enum):
    Accelerometer = 1
    Gyroscope = 2
    Magnetometer = 3
    DigitalRead = 4
    AnalogRead = 5

class OutputType(Enum):
    DigitalWrite = 1
    AnalogWrite = 2
    Screen = 3

class EventType(Enum):
    Init = 1
    ScreenInit = 2
    Print = 3
    Wifi = 4
    Gps = 5

### REQUEST CLASSES
class Request:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.is_input = False # Default for base class
        self.is_output = False # Default for base class
        self.is_event = False # Default for base class
        self.is_valid = True  # Default for base class


# Subclass for requests that require data in response
class InputRequest(Request):
    def __init__(self, timestamp, data_type, channels=[None], analog_params=None):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = data_type # Should be InputType
        self.channels = channels # List of hashable elements (e.g. ['x', 'y', 'z'])
        self.analog_params = analog_params


# Subclass for requests that are reporting system outputs
class OutputRequest(Request):
    def __init__(self, timestamp, data_type, values, channels=[None], analog_params=None):
        super().__init__(timestamp)
        self.is_output = True # Override default
        self.data_type = data_type # Should be OutputType
        self.values = values # Should be list of values
        self.channels = channels # Should be list of channel (corresponds with values)
        self.analog_params = analog_params


# Subclass for requests that are reporting internal system events
class EventRequest(Request):
    def __init__(self, timestamp, data_type, arg=None):
        super().__init__(timestamp)
        self.is_event = True # Override default
        self.data_type = data_type # Should be EventType
        self.arg = arg # Any additional data


# Subclass for invalid requests
class InvalidRequest(Request):
    def __init__(self, timestamp, arg=None):
        super().__init__(timestamp)
        self.is_valid = False # Override default
        self.arg = arg # Additional data
