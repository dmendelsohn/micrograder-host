from . import utils
from .communication import SerialCommunication
from .response import ErrorResponse

import numpy as np

def run_test(test_case, verbose=False):
    sc = SerialCommunication()
    sc.wait_for_connection()

    if verbose:
        print("Starting Test")
    while True:
        request = sc.get_request()
        if verbose:
            print(request)
        if request.is_valid:
            response = test_case.update(request)
        else:
            response = ErrorResponse()

        if verbose:
            print(response)
        sc.send_response(response)
        if response.is_error or response.test_complete:
            break

    if verbose:
        print("Assessing")
    return test_case.assess()

def main(filepath, verbose=False):
    #np.set_printoptions(threshold=np.nan)  # Uncomment for full array printing
    case = utils.load(filepath)
    result = run_test(case, verbose)
    print("Result:")
    print(result)