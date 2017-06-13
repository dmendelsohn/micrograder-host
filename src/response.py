### Response class and subclasses
class Response:  # Superclass for all responses
    def is_error(self):
        raise NotImplementedError("Subclass must implement this")

    def get_body(self):
        raise NotImplementedError("Subclass must implement this")

class AckResponse(Response):  # Superclass for all non-error responses
    def is_error():
        return False

class ErrorResponse(Response):
    def is_error(self):
        return True

    def get_body(self):
        return bytes() # Empty body, maybe later errors will have richer structure

# Below are responses for individual input types
class AccelerometerResponse(AckResponse):
    def __init__(self, values): # values is 3-tuple of ints for x, y and z axes respectively
        self.values = values

    def get_values():
        return self.values


class GyroscopeResponse(AckResponse):
    def __init__(self, values): # values is 3-tuple of ints for x, y and z axes respectively
        self.values = values

    def get_values(self):
        return self.values

class MagnetometerResponse(AckResponse):
    def __init__(self, values): # values is 3-tuple of ints for x, y and z axes respectively
        self.values = values

    def get_values(self):
        return self.values

class DigitalReadResponse(AckResponse):
    def __init__(self, value): # value is 1 or 0 (HIGH or LOW)
        self.value = value

    def get_value(self):
        return self.value

class AnalogReadResponse(AckResponse):
    def __init__(self, value): # value is an int
        self.value = value

    def get_value(self):
        return self.value

