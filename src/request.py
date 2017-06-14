from enum import Enum

class InputType(Enum):
    Accelerometer = 1
    Gyroscope = 2
    Magnetometer = 3
    DigitalRead = 4
    AnalogRead = 5

class OutputType(Enum):
    DigitalWrite = 1
    AnalogWrite = 2
    ScreenFull = 3
    ScreenTile = 4  # Not yet supported, this is for the future

AnalogParams = namedtuple('AnalogParams', ['min_bin', 'max_bin', 'min_value', 'max_value'])

### REQUEST CLASSES
class Request:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.is_input = False # Default for base class
        self.is_output = False # Default for base class
        self.is_event = False # Default for base class
        self.is_valid = True  # Default for base class
    

# Inputs
class AccelerometerRequest(Request):
    # analog params is named tuple with min_bin, max_bin, min_value, max_value
    def __init__(self, timestamp, analog_params):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = InputType.Accelerometer
        self.analog_params = analog_params

class GyroscopeRequest(Request):
    # analog params is named tuple with min_bin, max_bin, min_value, max_value
    def __init__(self, timestamp, analog_params):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = InputType.Gyroscope
        self.analog_params = analog_params

class MagnetometerRequest(Request):
    # analog params is named tuple with min_bin, max_bin, min_value, max_value
    def __init__(self, timestamp, analog_params):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = InputType.Magnetometer
        self.analog_params = analog_params

class DigitalReadRequest(Request):
    def __init__(self, timestamp, pin):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = InputType.DigitalRead
        self.pin = pin

class AnalogReadRequest(Request):
    # analog params is named tuple with min_bin, max_bin, min_value, max_value
    def __init__(self, timestamp, analog_params, pin):
        super().__init__(timestamp)
        self.is_input =  True # Override default
        self.analog_params = analog_params
        self.pin = pin

# Outputs 
class DigitalWriteRequest(Request):
    def __init__(self, timestamp, pin, value):
        super().__init__(timestamp)
        self.is_output = True # Override default
        self.data_type = OutputType.DigitalWrite
        self.pin = pin
        self.value = value

class AnalogWriteRequest(Request):
    def __init__(self, timestamp, analog_params, pin, value):
        super().__init__(timestamp)
        self.is_output = True # Override default
        self.data_type = OutputType.AnalogWrite
        self.analog_params = analog_params
        self.pin = pin
        self.value = value

class ScreenRequest(Request):
    def __init__(self, timestamp, screen):
        super().__init__(timestamp)
        self.is_output = True # Override default
        self.data_type = OuputType.ScreenFull
        self.screen = screen

# Events
class ScreenInitRequest(Request):
    # Width and height are screen dimensions in 8x8 "tiles"
    # E.g. 128x64 screen has width=16 and height=8
    def __init__(self, timestamp, width, height):
        super().__init__(timestamp)
        self.is_event = True # Override default
        self.width = width
        self.height = height

class InitRequest(Request):
    def __init__(self, timestamp):
        super().__init__(timestamp)
        self.is_event = True # Override default

class PrintRequest(Request):
    def __init__(self, timestamp, string):
        super().__init__(timestamp)
        self.is_event = True # Override default
        self.string = string

class GpsRequest(Request):
    def __init__(self, timestamp):
        super().__init__(timestamp)
        self.is_event = True # Override default

class WifiRequest(Request):
    def __init__(self, timestamp):
        super().__init__(timestamp)
        self.is_event = True # Override default

class InvalidRequest(Request):
    def __init__self(self, timestamp):
        super().__init__(timestamp)
        self.is_valid = False # Override default