from . import utils
from .case import TestCase
from .response import AckResponse
from .response import ErrorResponse

# Class for storing relevant information during an interactive recording session
class Recording:
    def __init__(self, conditions):
        self.conditions = conditions # List of conditions
        self.sequences = {} # Maps (data_type,channel)->ValueSequence

    # Updates each condition, and makes a record of the request
    # Returns None
    def update(request):
        for condition in self.conditions:
            condition.update(request)
        #TODO: make record

# Performs an interactive recording session
# Input: conditions is a list of conditions that will get updated with each request
#   information about when conditions are met will later be used to construct Frames
# Returns: Recording
def record(conditions, verbose=False):
    sc = SerialCommunication()
    sc.wait_for_connection()

    recording = Recording(conditions)

    if verbose:
        print("Starting recording")
    while True:
        request = sc.get_request()
        if verbose:
            print(request)
        recording.update(request)

        if not request.is_valid:
            response = ErrorResponse()
        elif request.is_input and request.values is None: # Not a recording
            response = ErrorResponse() # We shouldn't see these while recording
        else:
            response = AckResponse()

        if verbose:
            print(response)
        sc.send_response(response)

        if response.is_error: # TODO: or its been forever since a request
            break

    return recording
            

#TODO: description
def build_test_case(recording, verbose=False):
    # TODO: return a TestCase
    return None

def main(filepath, verbose=False):
    print("Record called with filepath={}".format(filepath))
    recording = record(verbose)
    case = build_test_case(recording, verbose)
    utils.save(case, filepath)