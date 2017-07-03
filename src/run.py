from . import utils
from .communication import SerialCommunication
from .log import RequestLog

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

        response = handler.update(request)
        if verbose:
            print("Response={}".format(response))
        sc.send_response(response)
        if response.is_error or response.complete:
            break

    if verbose:
        print("Session complete")
    return log

# Runs the RequestHandler saved at handler_filepath
# If log_filepath is not None, RequestLog is saved there
# timeout is in seconds, float okay
# Returns: RequestLog
def main(test_case_filepath, log_filepath, *, verbose=False, timeout=None):
    test_case = utils.load(test_case_filepath)
    handler = test_case.handler
    log = run_session(handler, verbose=verbose, timeout=timeout)
    if log_filepath:
        utils.save(log, log_filepath)
    return log