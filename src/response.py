### Response classes
class AckResponse:  # Superclass for all non-error responses
    def __init__(self):
        self.is_error = False

class ErrorResponse:
    def __init__(self):
        self.is_error = True

class AnalogValuesResponse(AckResponse):
    def __init__(self, values): # values is iterable of ints
        super().__init__()
        self.values = values

class DigitalValuesResponse(AckResponse):
    def __init__(self, values): # values is iterable of ints
        super().__init__()
        self.values = values


