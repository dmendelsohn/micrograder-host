from comm import SerialCommunication
from response import ErrorResponse

def run_test(test):
    sc = SerialCommunication()
    output_log = OutputLog()

    while not sc.connect():
        # Do nothing, wait for connection
        pass

    print("Starting Test")
    while True:
        sc.get_request()
        if request.is_valid:
            response, frame_id = test.update(request)
        else:
            response, frame_id = ErrorResponse(), -1

        sc.send_response(response)
        if response.is_error or response.test_complete:
            break

    print("Test finished, evaluating")
    return test.assess()