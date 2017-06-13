import struct
import serial
from serial import SerialException
from enum import Enum



# COM port parameters
ADDR = '/dev/cu.usbmodem1880221'
BAUD = 115200

# Communication constants
CODE_BYTES = 1 # 1 byte unsigned int for message code
TIMESTAMP_BYTES = 4 # 4 byte unsigned int for timestampe
MSG_SIZE_BYTES = 2 #2 byte unsigned int message size

class MessageCode(Enum):
    # Byte codes for system-level stuff
    INIT = 0x00
    PRINT = 0x01

    # Byte codes for GPIO
    DIGITAL_READ = 0x20
    DIGITAL_WRITE = 0x21
    ANALOG_READ = 0x22
    ANALOG_WRITE = 0x23

    # Byte codes for IMU
    IMU_ACC = 0x30
    IMU_GYRO = 0x31
    IMU_MAG = 0x32

    # Byte codes for OLED
    OLED_INIT = 0x40
    OLED_FULL = 0x41
    OLED_TILE = 0x42

    # Byte codes for GPS
    GPS_FIX = 0x50

    # Byte codes for Wifi events
    WIFI_REQ = 0x60
    WIFI_RESP = 0x61

    # Byte codes for responses
    ACK = 0x80
    ERR = 0x81


def bytes_to_request(msg_code, msg_body):
    #TODO: implement

def response_to_bytes(response):
    if response.is_error():
        msg_code = MessageCode.ERR
    else:
        msg_code = MessageCode.ACK

    #TODO: create msg_body
    return msg_code, msg_body

class SerialCommunication:
    def __init__(self):
        self.ser = None

    def connect(self):
        try:
            self.ser = serial.Serial(ADDR, BAUD)
            return True
        except SerialException:
            self.ser = None
            return False

    def get_request(self):
        header = self.ser.read(CODE_BYTES + TIMESTAMP_BYTES + MSG_SIZE_BYTES) # Read header
        msg_code = decode_int(header[:CODE_BYTES], signed=False)
        timestamp = decode_int(header[CODE_BYTES:CODE_BYTES+TIMESTAMP_BYTES], signed=False)
        msg_size = decode_int(header[CODE_BYTES+TIMESTAMP_BYTES:], signed=False)
        if msg_size > 0:
            msg_body = self.ser.read(msg_size)
        else:
            msg_body = bytes()
        return bytes_to_request(msg_code, msg_body)

    def send_response(response):
        msg_code, msg_body = response_to_bytes(response)
        to_send = utils.encode_int(msg_code, CODE_BYTES, signed=False)
        to_send += utils.encode_int(len(msg_body), MSG_SIZE_BYTES, signed=False)
        to_send += msg_body
        self.ser.write(to_send)  # Must send it all at once, so it's in the same USB packet
