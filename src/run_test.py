from comm import SerialCommunication
from response import ErrorResponse
from test import LogEntry

def run_test(test):
    sc = SerialCommunication()
    test_log = [] # List, elements of type LogEntry
    while not sc.connect():
        # Do nothing, wait for connection
        pass

    while True:
        sc.get_request()
        if request.is_valid:
            response, frame_id = test.update(request)
        else:
            response, frame_id = ErrorResponse(), -1

        test_log.append(LogEntry(request=request, response=response, frame_id=frame_id))
        sc.send_response(response)
        if response.is_error or response.test_complete:
            break

    return test_log