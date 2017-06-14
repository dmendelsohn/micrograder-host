### Response classes
class AckResponse:  # Superclass for all non-error responses
    def __init__(self):
        self.is_error = False

class ErrorResponse:
    def __init__(self):
        self.is_error = True
        self.test_complete = True  # Give up when an error occurs

class AnalogValuesResponse(AckResponse):
    def __init__(self, values, test_complete=False): # values is iterable of ints
        super().__init__()
        self.values = values
        self.test_complete = test_complete

class DigitalValuesResponse(AckResponse):
    def __init__(self, values, test_complete=False): # values is iterable of ints
        super().__init__()
        self.values = values
        self.test_complete = test_complete


