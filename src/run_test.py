from . import utils
from .communication import SerialCommunication
from .response import ErrorResponse

import numpy as np

def run_test(test_case):
    sc = SerialCommunication()
    sc.wait_for_connection()

    total_log = []
    print("Starting Test")
    while True:
        request = sc.get_request()
        print(request)
        if request.is_valid:
            response = test_case.update(request)
        else:
            response = ErrorResponse()

        print(response)
        sc.send_response(response)
        total_log.append((request, response))
        if response.is_error or response.test_complete:
            break

    print("Assessing")
    return test_case.assess()

def main(filepath):
    #np.set_printoptions(threshold=np.nan)  # Uncomment for full array printing
    case = utils.load(filepath)
    result = run_test(case)
    print("Result:")
    print(result)