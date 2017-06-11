import struct
import serial
from serial import SerialException
from collections import namedtuple


# COM port parameters
ADDR = '/dev/cu.usbmodem1880221'
BAUD = 115200
ser = None

# Communication constants
CODE_BYTES = 1 # 1 byte unsigned int for message code
TIMESTAMP_BYTES = 4 # 4 byte unsigned int for timestampe
MSG_SIZE_BYTES = 2 #2 byte unsigned int message size


FORMAT_CHARS = {
    (1,False): 'B', (1,True): 'b',
    (2,False): 'H', (2,True): 'h',
    (4,False): 'I', (4,True): 'i',
    (8,False): 'Q', (8,True): 'q'
}

def connect():
    global ser
    try:
        ser = serial.Serial(ADDR, BAUD)
        return True
    except SerialException:
        ser = None
        return False

def read_message():
    header = ser.read(CODE_BYTES + TIMESTAMP_BYTES + MSG_SIZE_BYTES) # Read header
    code = decode_int(header[:CODE_BYTES], signed=False)
    timestamp = decode_int(header[CODE_BYTES:CODE_BYTES+TIMESTAMP_BYTES], signed=False)
    msg_size = decode_int(header[CODE_BYTES+TIMESTAMP_BYTES:], signed=False)
    if msg_size > 0:
        body = ser.read(msg_size)
    else:
        body = bytes()
    return Request(code=code, timestamp=timestamp, body=body)

def send_message(response):
    to_send = encode_int(response.code, CODE_BYTES, signed=False)
    to_send += encode_int(len(response.body), MSG_SIZE_BYTES, signed=False)
    to_send += response.body
    ser.write(to_send)  # Must send it all at once, so it's in the same USB packet

# Decodes an integer from bytes, little-endian and returns it as an int
# raw_bytes must be of length 1, 2, 4, 8
def decode_int(raw_bytes, signed=False):
    width = len(raw_bytes)
    if (width,signed) in FORMAT_CHARS:
        format_char = FORMAT_CHARS[(width,signed)]
        try:
            return struct.unpack('<' + format_char, raw_bytes)[0]
        except struct.error as e:
            raise e
    else:
        raise ValueError('Could not decode {} with signed={}'.format(raw_bytes, signed))

# Encodes an integer (num) as bytes, little-endian.  Note that width is byte-width, not bit-width
# width must be 1, 2, 4, or 8
def encode_int(num, width=4, signed=False):
    if (width,signed) in FORMAT_CHARS:
        format_char = FORMAT_CHARS[(width,signed)]
        try:
            return struct.pack('<' + format_char, num)
        except struct.error as e:
            raise e
    else:
        raise ValueError('Invalid encode width={} bytes with signed = {}'.format(width, signed))


