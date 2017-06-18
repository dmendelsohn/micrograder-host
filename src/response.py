### Response classes
class AckResponse:  # Superclass for all non-error responses
    def __init__(self, test_complete=False):
        self.is_error = False
        self.test_complete = test_complete

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

class ErrorResponse:
    def __init__(self, test_complete=False):
        self.is_error = True
        self.test_complete = test_complete  # Give up when an error occurs

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return "ErrorResponse: test_complete={}".format(self.test_complete)

class ValuesResponse(AckResponse):
    def __init__(self, values, analog, test_complete=False): # values is iterable of ints
        super().__init__(test_complete)
        self.values = values
        self.analog = analog # True for analog, False for digital

    def __str__(self):
        return "ValuesResponse: values={}, analog={}".format(self.values, self.analog)