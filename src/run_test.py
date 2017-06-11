import comm
import utils
from utils import MessageCode
from utils import Request
from utils import Response


# Assume connection is made
# TODO: more descriptive error handling
def run_test(test):
    prev_frame_id = None
    while True:
        is_error = False
        new_frame_id = None
        req = comm.read_message()
        test.update(req)
        if req.is_input():
            resp_body, new_frame_id = test.get_response(req)
        elif req.is_output() or req.is_event():
            resp_body = bytes()
        else:
            is_error = True
            resp_body = bytes('Bad code'.encode('ascii'))

        if resp_body is None:
            is_error = True
            resp_body = bytes('No response possible'.encode('ascii'))
 

        resp_code = MessageCode.ACK
        if is_error:
            resp_code = MessageCode.ERR
        resp = Response(resp_code, resp_body)
        comm.send_message(resp)

        #DEBUG
        print("Received request: {}".format(req))
        print("Sent response {}".format(resp))