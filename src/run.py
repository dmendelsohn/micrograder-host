from . import utils
from .communication import SerialCommunication
from .log import RequestLog
from .utils import EventType

import numpy as np

# Runs an interactive session with the embedded side
# Input: handler is a RequestHandler
#   timeout: the timeout in seconds (float ok)
# Returns: RequestLog
def run_session(handler, *, verbose=False, timeout=None):
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
        elif request.data_type == EventType.Print:
            print("Debug: {}".format(request.arg))

        response = handler.update(request)
        if verbose:
            print("Response={}".format(response))
        sc.send_response(response)
        if response.is_error or response.complete:
            if response.is_error:
                print(request)
                print(response)
            break

    if verbose:
        print("Session complete")
    return log