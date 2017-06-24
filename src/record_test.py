from . import utils
from .case import TestCase
from .response import AckResponse
from .response import ErrorResponse

#TODO: description
def record(verbose=False):
    sc = SerialCommunication()
    sc.wait_for_connection()

    # TODO: initialize log
    if verbose:
        print("Starting recording")
    while True:
        request = sc.get_request()
        if verbose:
            print(request)

        if not request.is_valid:
            response = ErrorResponse()
        elif request.is_input and request.values is None: # Not a recording
            response = ErrorResponse() # We shouldn't see these while recording
        else:
            response = AckResponse()

        if verbose:
            print(response)
        sc.send_response(response)

        #TODO: update log

        if response.is_error: #TODO: or "DONE_RECORDING" event
            break

    #TODO: return log
    return None
            

#TODO: description
def build_test_case(recording, verbose=False):
    # TODO: return a TestCase
    return None

def main(filepath, verbose=False):
    print("Record called with filepath={}".format(filepath))
    recording = record(verbose)
    case = build_test_case(recording, verbose)
    utils.save(case, filepath)