from enum import Enum

class InputType(Enum):
    Accelerometer = 1
    Gyroscope = 2
    Magnetometer = 3
    DigitalRead = 4
    AnalogRead = 5

class OutputType(Enum):
    Screen = 1
    DigitalWrite = 2
    AnalogWrite = 3

### REQUEST CLASSES
class Request:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.is_input = False # Default for base class
        self.is_output = False # Default for base class
        self.is_event = False # Default for base class
    

class AccelerometerRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = InputType.Accelerometer
        #TODO: process args

class GyroscopeRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = InputType.Gyroscope
        #TODO: process args

class MagnetometerRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = InputType.Magnetometer
        #TODO: process args

class DigitalReadRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        self.is_input = True # Override default
        self.data_type = InputType.DigitalRead
        #TODO: process args

class AnalogReadRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        self.is_input =  True # Override default
        #TODO: process args

class ScreenRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        self.is_output = True # Override default
        self.data_type = OutputType.Screen
        #TODO: process args   

class DigitalWriteRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        self.is_output = True # Override default
        self.data_type = OutputType.DigitalWrite
        #TODO: process args

class AnalogWriteRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        self.is_output = True # Override default
        self.data_type = OutputType.AnalogWrite
        #TODO: process args  

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
