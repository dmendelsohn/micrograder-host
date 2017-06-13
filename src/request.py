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

### REQUEST CLASSES
class Request:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.is_input = False # Default for base class
        self.is_output = False # Default for base class
        self.is_event = False # Default for base class
    

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

class GPSRequest(Request):
    def __init__(self, timestamp):
        super().__init__(timestamp)
        self.is_event = True # Override default

class WifiRequest(Request):
    def __init__(self, timestamp):
        super().__init__(timestamp)
        self.is_event = True # Override default

class SystemRequest(Request):
    def __init__(self, timestamp):
        super().__init__(timestamp)
        self.is_event = True # Override default
