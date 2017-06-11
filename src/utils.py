# Later: reorganize this into more logical modules
from enum import Enum


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

INPUT_CODES = set(
    MessageCode.MG_DIGITAL_READ,
    MessageCode.MG_ANALOG_READ,
    MessageCode.MG_IMU_ACC,
    MessageCode.MG_IMU_GYRO,
    MessageCode.MG_IMU_MAG)

OUTPUT_CODES = set(
    MessageCode.MG_DIGITAL_WRITE,
    MessageCode.MG_ANALOG_WRITE,
    MessageCode.MG_OLED_FULL,
    MessageCode.MG_OLED_TILE)

EVENT_CODES = set(
    MessageCode.MG_INIT,
    MessageCode.MG_PRINT,
    MessageCode.MG_OLED_INIT,
    MessageCode.MG_GPS_FIX,
    MessageCode.MG_WIFI_REQ,
    MessageCode.MG_WIFI_RESP)

RESPONSE_CODES = set(
    MessageCode.MG_ACK,
    MessageCode.MG_ERR)

class Request:
    def __init__(self, msg_code, timestamp, body):
        self.msg_code = msg_code
        self.timestamp = timestamp
        self.body = body

    def is_input(self):
        return self.msg_code in INPUT_CODES

    def is_output(self):
        return self.msg_code in OUTPUT_CODES

    def is_event(self):
        return self.msg_code in EVENT_CODES
        

class Response:
    def __init__(self, msg_type, body):
        self.msg_type = msg_type
        self.body = body


class Test:
    # iterable of Frames, and tracking when Frames are in use