### Response classes
class AckResponse:  # Superclass for all non-error responses
    def __init__(self, test_complete=False):
        self.is_error = False
        self.test_complete = test_complete

class ErrorResponse:
    def __init__(self, test_complete=False):
        self.is_error = True
        self.test_complete = test_complete  # Give up when an error occurs

class AnalogValuesResponse(AckResponse):
    def __init__(self, values, test_complete=False): # values is iterable of ints
        super().__init__(test_complete)
        self.values = values

class DigitalValuesResponse(AckResponse):
    def __init__(self, values, test_complete=False): # values is iterable of ints
        super().__init__(test_complete)
        self.values = values


