### REQUEST CLASSES
class Request:
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def is_input(self):
        return False # Default for base class

    def is_output(self):
        return False # Default for base class

    def is_event(self):
        return False # Default for base class
    

class AccelerometerRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_input(self):
        return True # Override default

class GyroscopeRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_input(self):
        return True # Override default

class MagnetometerRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_input(self):
        return True # Override default

class DigitalReadRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_input(self):
        return True # Override default

class AnalogReadRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_input(self):
        return True # Override default

class DigitalWriteRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_output(self):
        return True # Override default

class AnalogWriteRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_output(self):
        return True # Override default

class ScreenRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_output(self):
        return True # Override default      

class GPSRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_event(self):
        return True # Override default

class WifiRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_event(self):
        return True # Override default

class SystemRequest(Request):
    def __init__(self, timestamp, ...):
        super().__init__(timestamp)
        #TODO: process args

    def is_event(self):
        return True # Override default