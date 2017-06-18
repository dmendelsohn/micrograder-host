from src.communication import *
from src.request import EventRequest
from src.request import EventType
from src.request import InputRequest
from src.request import InputType
from src.request import InvalidRequest
from src.request import OutputRequest
from src.request import OutputType
from src.response import AckResponse
from src.response import ErrorResponse
from src.response import ValuesResponse
from src.screen import Screen
from src.screen import ScreenShape
from src.utils import AnalogParams

import numpy as np
import unittest

class TestSerialCommunication(unittest.TestCase):
    def setUp(self):
        self.sc = SerialCommunication()

    def test_bytes_to_request_digital(self):
        t = 1000 # Arbitrary timestamp

        code = 0x20  # Digital read
        body = bytes([255]) # pin 255
        expected = InputRequest(t, InputType.DigitalRead, [255])
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x21  # Digital write
        body = bytes([255, 1]) # pin 255, value 1
        expected = OutputRequest(t, OutputType.DigitalWrite, [1], [255])
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

    def test_bytes_to_request_analog(self):  # Except for screen output requests
        t = 1000 # Arbitrary timestamp
        b = bytes([254, 255, 255, 255,
                        255, 255, 255, 255,
                        0, 0, 0, 0,
                        1, 0, 0, 0])
        params = AnalogParams(min_bin=-2, max_bin=-1, min_value=0, max_value=1)

        code = 0x22 # Analog Read
        body = bytes([255]) + b
        expected = InputRequest(t, InputType.AnalogRead, [255], params)
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x23 # Analog Write
        body = bytes([255]) + b + bytes([255, 255, 255, 255])
        expected = OutputRequest(t, OutputType.AnalogWrite, [-1], [255], params)
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x30 # Acc
        body = b
        expected = InputRequest(t, InputType.Accelerometer, ['x','y','z'], params)
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x31 # Gyro
        body = b
        expected = InputRequest(t, InputType.Gyroscope, ['x','y','z'], params)
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x32 # Mag
        body = b
        expected = InputRequest(t, InputType.Magnetometer, ['x','y','z'], params)
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

    def test_bytes_to_request_event(self):
        t = 1000 # Arbitrary timestamp

        code = 0x00 # Init
        expected = EventRequest(t, EventType.Init)
        self.assertEqual(self.sc.bytes_to_request(code, t, bytes()), expected)

        code = 0x01 # Print
        body = bytes([102, 111, 111])
        expected = EventRequest(t, EventType.Print, 'foo')
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x50 # GpsFix
        expected = EventRequest(t, EventType.Gps)
        self.assertEqual(self.sc.bytes_to_request(code, t, bytes()), expected)

        code = 0x60 # WifiReq
        expected = EventRequest(t, EventType.Wifi)
        self.assertEqual(self.sc.bytes_to_request(code, t, bytes()), expected)

        code = 0x61 # WifiResp
        expected = EventRequest(t, EventType.Wifi)
        self.assertEqual(self.sc.bytes_to_request(code, t, bytes()), expected)

    def test_bytes_to_request_screen(self):
        t = 1000 # Arbitrary timestamp

        code = 0x42 # ScreenTile
        body = bytes([0, 0] + [255]*8)
        expected = InvalidRequest(t) # No init yet
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x40 # ScreenInit
        body = bytes([2,1]) # one tiles wide, one high
        expected = EventRequest(t, EventType.ScreenInit, ScreenShape(16,8))
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x40 # ScreenInit
        body = bytes([2,1]) # one tiles wide, one high
        expected = InvalidRequest(t) # Second init is invalid
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x41 # ScreenFull
        body = bytes([255] + [129]*14 + [255]) # Border around 16x8 screen
        buff = np.zeros((8, 16))
        buff[0,:] = 1 # Top
        buff[7,:] = 1 # Bottom
        buff[:,0] = 1 # Left
        buff[:,15] = 1 # Right
        expected = OutputRequest(t, OutputType.Screen, [Screen(buff=buff)])
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x42 # ScreenTile
        body = bytes([0,0] + [255]*8) # Light up entire left tile
        buff[:,0:8] = 1
        expected = OutputRequest(t, OutputType.Screen, [Screen(buff=buff)])
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)


    def test_response_to_bytes(self):
        resp = AckResponse(test_complete=False)
        expected = 0x80, bytes()
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = AckResponse(test_complete=True)
        expected = 0x81, bytes()
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = ErrorResponse(test_complete=False)
        expected = 0x82, bytes()
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = ErrorResponse(test_complete=True)
        expected = 0x83, bytes()
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = ValuesResponse(values=[1,0,1], analog=False, test_complete=False)
        expected = 0x80, bytes([1,0,1])
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = ValuesResponse(values=[-2,-1,65535], analog=True, test_complete=True)
        expected = 0x81, bytes([254, 255, 255, 255, 255, 255, 255, 255, 255, 255, 0, 0])
        self.assertEqual(self.sc.response_to_bytes(resp), expected)
