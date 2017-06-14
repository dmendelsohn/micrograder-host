from comm import SerialCommunication
from response import ErrorResponse
from test import TestLog


# Assume connection is made
# TODO: more descriptive error handling
def run_test(test):
    sc = SerialCommunication()
    tl = TestLog()
    while not sc.connect():
        # Do nothing, wait for connection
        pass

    while True:
        sc.get_request()
        if request.is_valid:
            response, frame_id = test.update(request)
        else:
            response, frame_id = ErrorResponse(), -1

        tl.log(request, response, frame_id)
        sc.send_response(response)
        if response.test_complete:
            break

        #DEBUG
        #print("Received request: {}".format(req))
        #print("Sent response {}".format(resp))