from . import utils
from .communication import SerialCommunication
from .log import RequestLog

import numpy as np
import datetime

DEFAULT_TIMEOUT = datetime.timedelta(seconds=30)

# Runs an interactive session with the embedded side
# Input: handler is a RequestHandler
# Returns: RequestLog
def run_session(handler, *, verbose=False, timeout=DEFAULT_TIMEOUT):
    sc = SerialCommunication()
    sc.wait_for_connection()

    log = RequestLog()

    if verbose:
        print("Starting session")
    while True:
        request = sc.get_request(timeout)
        if request is None: # There was an exception or timeout
            if verbose:
                print("Serial exception or timeout")
            break

        log.update(request)
        if verbose:
            print("Request={}".format(request))

        response = handler.update(request)
        if verbose:
            print("Response={}".format(response))
        sc.send_response(response)
        if response.is_error or response.complete:
            break

    if verbose:
        print("Session complete")
    return log

def build_test_case(log, verbose=False):
    #TODO: implement
    pass

# TODO: make this the entry point for both RECORDING and TESTING
def main(filepath, verbose=False):
    #TODO: implement
    pass