from collections import namedtuple

from . import utils
from .utils import BatchParams
from .utils import EventType
from .utils import InputType
from .utils import OutputType

THREE_AXIS = ['x', 'y', 'z']  # Standard channels for three axis quantities

### REQUEST CLASSES
class Request:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.is_input = False # Default for base class
        self.is_output = False # Default for base class
        self.is_event = False # Default for base class
        self.is_measure = False # Default for base class
        self.is_valid = True  # Default for base class
        self.data_type = None

    def __eq__(self, other):
        return type(self) is type(other) and self.__dict__ == other.__dict__


# Subclass for requests that require data in response
class InputRequest(Request):
    # For recordings, len(values) must equal len(channels)*batch_params.num
    # For non-recordingds, values must be None
    def __init__(self, timestamp, data_type, channels, *,
                 values=None, analog_params=None, batch_params=BatchParams(num=1, period=0)):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = data_type # Should be InputType
        self.channels = channels # List of hashable elements (e.g. ['x', 'y', 'z'])
        self.values = values
        self.analog_params = analog_params
        self.batch_params = batch_params

    def __str__(self):
        s = "InputRequest: timestamp={}, data_type={}, channels={}, values={}, analog_params={}"
        return s.format(self.timestamp, self.data_type, self.channels, self.values,
                        self.analog_params)


# Subclass for requests that are reporting system outputs
class OutputRequest(Request):
    def __init__(self, timestamp, data_type, channels, values, analog_params=None):
        super().__init__(timestamp)
        self.is_output = True # Override default
        self.data_type = data_type # Should be OutputType
        self.channels = channels # Should be list of channel (corresponds with values)
        self.values = values # Should be list of values
        self.analog_params = analog_params
        self.batch_params = BatchParams(num=1, period=0)

    def __str__(self):
        s = "OutputRequest: timestamp={}, data_type={}, channels={}, values={}, analog_params={}"
        return s.format(self.timestamp, self.data_type, self.channels, self.values,
                        self.analog_params)

# Subclass for requests that are reporting internal system events
class EventRequest(Request):
    def __init__(self, timestamp, data_type, data=None):
        super().__init__(timestamp)
        self.is_event = True # Override default
        self.data_type = data_type # Should be EventType
        self.data = data # Any additional data

    def __str__(self):
        s = "EventRequest: timestamp={}, data_type={}, data={}"
        return s.format(self.timestamp, self.data_type, self.data)


# Subclass for invalid requests
class InvalidRequest(Request):
    def __init__(self, timestamp, data=None):
        super().__init__(timestamp)
        self.is_valid = False # Override default
        self.data = data # Additional data

    def __str__(self):
        return "InvalidRequest: timestamp={}, data={}".format(self.timestamp, self.data)
