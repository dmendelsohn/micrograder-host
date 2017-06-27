### Response classes
class AckResponse:  # Superclass for all non-error responses
    def __init__(self, complete=False):
        self.is_error = False
        self.complete = complete

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return "AckResponse: complete={}".format(self.complete)

class ErrorResponse:
    def __init__(self, complete=False):
        self.is_error = True
        self.complete = complete  # Give up when an error occurs

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return "ErrorResponse: complete={}".format(self.complete)

class ValuesResponse(AckResponse):
    def __init__(self, values, analog, complete=False): # values is iterable of ints
        super().__init__(complete)
        self.values = values
        self.analog = analog # True for analog, False for digital

    def __str__(self):
        string = "ValuesResponse: values={}, analog={}, complete={}"
        return string.format(self.values, self.analog, self.complete)
