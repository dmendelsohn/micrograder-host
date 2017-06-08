import comm
import random

def run_test():
    connected = comm.connect()
    if not connected:
        #TODO: error or retry
        print("Failed to connect")
        return

    while True:
        req = comm.read_message()
        if req.code == comm.MG_DIGITAL_READ:
            num = random.randint(0,1)
            body = comm.encode_int(num, width=1, signed=False)
        else:   
            body = bytes()
        resp = comm.Response(code=comm.MG_ACK, body=body)
        comm.send_message(resp)
        print("Received request: {}".format(req))
        print("Sent response {}".format(resp))

if __name__ == "__main__":
    run_test()