import serial
from serial import SerialException
from enum import Enum
from request import *
from response import *
import numpy as np


# COM port parameters
ADDR = '/dev/cu.usbmodem1880221'
BAUD = 115200

# Communication constants
CODE_BYTES = 1 # 1 byte unsigned int for message code
TIMESTAMP_BYTES = 4 # 4 byte unsigned int for timestampe
MSG_SIZE_BYTES = 2 #2 byte unsigned int message size
ANALOG_PARAMS_SIZE = 4*4

class MessageCode(Enum):
    # Byte codes for system-level stuff
    Init = 0x00
    Print = 0x01

    # Byte codes for GPIO
    DigitalRead = 0x20
    DigitalWrite = 0x21
    AnalogRead = 0x22
    AnalogWrite = 0x23

    # Byte codes for IMU
    ImuAcc = 0x30
    ImuGyro = 0x31
    ImuMag = 0x32

    # Byte codes for Screen
    ScreenInit = 0x40
    ScreenFull = 0x41
    ScreenTile = 0x42

    # Byte codes for GPS
    GpsFix = 0x50

    # Byte codes for Wifi events
    WifiReq = 0x60
    WifiResp = 0x61

    # Byte codes for responses
    Ack = 0x80
    Error = 0x81

class SerialCommunication:
    def __init__(self):
        self.ser = None
        self.last_screen = None # Tracks last screen, to allow for incremental messages

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

    # Input: bytes of length 16 and interpret as 4 int32s
    # Return: named tuple: min_bin, max_bin, min_value, max_value
    def decode_analog_params(raw):
        min_bin = utils.decode_int(raw[0:4], signed=True)
        max_bin = utils.decode_int(raw[4:8], signed=True)
        min_value = utils.decode_int(raw[8:12], signed=True)
        max_value = utils.decode_int(raw[12:16], signed=True)
        return AnalogParams(min_bin, max_bin, min_value, max_value)

    # Input: bytes of length 8
    # Return: 8x8 numpy array of uint8 (1 represents lit pixel)
    # Each byte of input corresponds to column of output, with MSB at top of column
    def decode_screen_tile(data):
        data = np.array([[elt] for elt in data], dtype=np.uint8)
        tile = np.unpackbits(data, axis=1)
        return tile.transpose()

    def bytes_to_request(msg_code, timestamp, msg_body):
        if msg_code == MessageCode.Init:  # Body: <> (empty)
            return InitRequest(timestamp)

        elif msg_code == MessageCode.Print: # <uint8 * chars>
            string = str(msg_body, encoding='utf-8')
            return PrintRequest(timestamp, string)

        elif msg_code == MessageCode.DigitalRead: # Body format: <uint8 pin>
            if len(msg_body) < 1:
                return InvalidRequest(timestamp)  # Not enough data
            pin = msg_body[0]
            return DigitalReadRequest(pin)

        elif msg_code == MessageCode.DigitalWrite: # <uint8 pin, uint8 val>
            if len(msg_body) < 2:
                return InvalidRequest(timestamp): # Not enough data
            pin = msg_body[0]
            value = msg_body[1]
            return DigitalWriteRequest(pin, value)

        elif msg_code == MessageCode.AnalogRead: #<uint8 pin, int32 min_bin, max_bin, min_val, max_val>
            if len(msg_body) < (1+ANALOG_PARAMS_SIZE):
                return InvalidRequest(timestamp) # Not enough data
            pin = msg_body[0]
            analog_params = decode_analog_params(msg_body[1:1+ANALOG_PARAMS_SIZE])
            return AnalogReadRequest(timestamp, analog_params, pin)

        elif msg_code == MessageCode.AnalogWrite: #<uint8 pin, int32 min_bin, max_bin, min_val, max_val, val>
            if len(msg_body) < (1+4+ANALOG_PARAMS_SIZE):
                return InvalidRequest(timestamp) # Not enough data
            pin = msg_body[0]
            analog_params = decode_analog_params(msg_body[1:1+ANALOG_PARAMS_SIZE])
            values_bytes = msg_body[(1+ANALOG_PARAMS_SIZE):(1+4+ANALOG_PARAMS_SIZE)]
            value = utils.decode_int(value_bytes, signed=True)
            return AnalogWriteRequest(timestamp, analog_params, pin, value)

        elif msg_code == MessageCode.ImuAcc: #<int32 min_bin, max_bin, min_val, max_val>
            if len(msg_body) < ANALOG_PARAMS_SIZE:
                return InvalidRequest(timestamp) # Not enough data
            analog_params = decode_analog_params(msg_body)
            return AccelerometerRequest(timestamp, analog_params)

        elif msg_code == MessageCode.ImuGyro: #<int32 min_bin, max_bin, min_val, max_val>
            if len(msg_body) < ANALOG_PARAMS_SIZE:
                return InvalidRequest(timestamp) # Not enough data
            analog_params = decode_analog_params(msg_body)
            return GyroscopeRequest(timestamp, analog_params)

        elif msg_code == MessageCode.ImuMag: #<int32 min_bin, max_bin, min_val, max_val>
            if len(msg_body) < ANALOG_PARAMS_SIZE:
                return InvalidRequest(timestamp) # Not enough data
            analog_params = decode_analog_params(msg_body)
            return MagnetometerRequest(timestamp, analog_params)

        elif msg_code == MessageCode.ScreenInit: # <uint8 tile_width, tile_height>
            if len(msg_body) < 2:
                return InvalidRequest(timestamp) # Not enough data
            tile_width = msg_body[0]
            tile_height = msg_body[1]
            self.last_screen = Screen(width=8*tile_width, height=8*tile_height)

        elif msg_code == MessageCode.ScreenFull: # <uint8 tile_width, tile_height, uint8 * buffer>
            # buffer is seq of 8 byte tiles.  Tiles are 8x8 pixels.  Tiles are organized by row
            if self.last_screen is None:
                return InvalidRequest(timestamp) # No screen initialization
            tile_width = (self.last_screen.shape[1]+7)//8
            tile_height = (self.last_screen.shape[0]+7)//8

            if len(msg_body) < (8*tile_width*tile_height):
                return InvalidRequest(timestamp) # Not enough data

            # Now we construct the screen
            screen = Screen(width=8*tile_width, height=8*tile_height) # Create empty buffer
            for x in range(tile_height): # x is in tiles, not pixels
                for y in range(tile_width): # y is in tiles, not pixels
                    start_index = 8*(y*tile_width + x)
                    tile = decode_screen_tile(msg_body[start_index:start_index+8])
                    screen.paint(rect=tile, x=8*x, y=8*y)

            self.last_screen = screen
            return ScreenRequest(timestamp, screen)

        elif msg_code == MessageCode.ScreenTile: # <uint8 x, uint8 y, uint8 tile[8]>
            # buffer is seq of 8 byte tiles.  Tiles are 8x8 pixels.  Tiles are organized by row
            if self.last_screen is None:
                return InvalidRequest(timestamp) # No screen initialization

            if len(msg_body) < 10:
                return InvalidRequest(timestamp) # Not enough data

            x = msg_body[0] # Measured in tiles, not pixels
            y = msg_body[1] # Measured in tiles, not pixels
            tile = decode_screen_tile(msg_body[2:10])
            self.last_screen.paint(rect=tile, x=8*x, y=8*y)

        elif msg_code == MessageCode.GpsFix: # Later: expand protocol
            return GpsRequest(timestamp)

        elif msg_code == MessageCode.WifiReq: # Later: expand protocol
            return WifiRequest(timestamp)

        elif msg_code == MessageCode.WifiResp: # Later: expand protocol
            return WifiRequest(timestamp)

        else:  # Invalid message code
            return InvalidRequest(timestamp)

    def response_to_bytes(response):
        if response.is_error:
            msg_code = MessageCode.Error
        else:
            msg_code = MessageCode.Ack

        if type(response) is AckResponse: # Ack without data
            msg_body = bytes()
        elif type(response) is ErrorResponse: # Error without data
            msg_body = bytes()
        elif type(response) is DigitalValuesResponse: # Sequence of digital values (uint8)
            msg_body = bytes()
            for value in response.values:
                msg_body += utils.encode_int(value, width=1, signed=False)
        elif type(response) is AnalogValuesResponse: # Sequence of analog values (int32)
            msg_body = bytes()
            for value in response.values:
                msg_body += utils.encode_int(value, width=4, signed=True)
        else: # Unsupported response type
            msg_code = MessageCode.Error
            msg_body = bytes()

        return msg_code, msg_body
