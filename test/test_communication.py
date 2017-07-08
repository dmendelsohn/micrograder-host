from src.communication import *
from src.request import EventRequest
from src.request import InputRequest
from src.request import InvalidRequest
from src.request import OutputRequest
from src.response import AckResponse
from src.response import ErrorResponse
from src.response import ValuesResponse
from src.screen import Screen
from src.screen import ScreenShape
from src.utils import AnalogParams
from src.utils import EventType
from src.utils import InputType
from src.utils import OutputType

import itertools
import numpy as np
import unittest

class TestSerialCommunication(unittest.TestCase):
    def setUp(self):
        self.sc = SerialCommunication()
        self.analog_bytes = bytes([254, 255, 255, 255,
                                255, 255, 255, 255,
                                0, 0, 0, 0,
                                1, 0, 0, 0])
        self.analog_params = AnalogParams(min_bin=-2, max_bin=-1, min_value=0, max_value=1)
        self.t = 1000 # Arbitrary timestamp


    def test_build_input_request(self):
        data_type = None # This just gets passed along
        channels = [0,1,2] # Only the length of this list matters
        batch_bytes = bytes([2, 0, 0, 1, 0, 0])
        batch_params = BatchParams(num=2, period=0.256)

        count = 0
        for (is_analog, is_batch, is_recording) in itertools.product([False, True], repeat=3):
            flag = 0 # Build up flag byte
            if is_batch:
                flag += 2
            if is_recording:
                flag += 1

            msg_body = bytes([flag])
            if is_analog:
                msg_body += self.analog_bytes
                a_params = self.analog_params
            else:
                a_params = None

            if is_batch:
                msg_body += batch_bytes
                b_params = batch_params
            else:
                b_params = BatchParams(num=1, period=0)

            if is_recording:
                if is_analog:
                    chunk = bytes([0,0,0,0, 1,0,0,0, 2,0,0,0])
                else:
                    chunk = bytes([0,1,2])
                if is_batch:
                    num_times = batch_params.num
                else:
                    num_times = 1
                msg_body += chunk*num_times
                expected_vals = [0,1,2]*num_times 
            else:
                expected_vals = None

            actual = self.sc.build_input_request(data_type, channels, is_analog, self.t, msg_body)

            expected = InputRequest(self.t, None, channels, values=expected_vals,
                                    analog_params=a_params, batch_params=b_params)

            self.assertEqual(actual, expected)

    def test_bytes_to_request_input(self):
        code = 0x20  # Digital read
        body = bytes([13]) + bytes([0])
        expected = InputRequest(self.t, InputType.DigitalRead, [13])
        self.assertEqual(self.sc.bytes_to_request(code, self.t, body), expected)

        code = 0x22 # Analog Read
        body = bytes([14]) + bytes([0]) + self.analog_bytes
        expected = InputRequest(self.t, InputType.AnalogRead, [14],
                                analog_params=self.analog_params)
        self.assertEqual(self.sc.bytes_to_request(code, self.t, body), expected)

        code = 0x30 # Acc
        body = bytes([0]) + self.analog_bytes
        expected = InputRequest(self.t, InputType.Accelerometer, ['x','y','z'],
                                analog_params=self.analog_params)
        self.assertEqual(self.sc.bytes_to_request(code, self.t, body), expected)

        code = 0x31 # Gyro
        body = bytes([0]) + self.analog_bytes
        expected = InputRequest(self.t, InputType.Gyroscope, ['x','y','z'],
                                analog_params=self.analog_params)
        self.assertEqual(self.sc.bytes_to_request(code, self.t, body), expected)

        code = 0x32 # Mag
        body = bytes([0]) + self.analog_bytes
        expected = InputRequest(self.t, InputType.Magnetometer, ['x','y','z'],
                                analog_params=self.analog_params)
        self.assertEqual(self.sc.bytes_to_request(code, self.t, body), expected)

    def test_bytes_to_request_output(self):  # Except for screen output requests
        code = 0x21  # Digital write
        body = bytes([255, 1]) # pin 255, value 1
        expected = OutputRequest(self.t, OutputType.DigitalWrite, [255], [1])
        self.assertEqual(self.sc.bytes_to_request(code, self.t, body), expected)

        code = 0x23 # Analog Write
        body = bytes([255]) + self.analog_bytes + bytes([255, 255, 255, 255])
        expected = OutputRequest(self.t, OutputType.AnalogWrite, [255], [-1], self.analog_params)
        self.assertEqual(self.sc.bytes_to_request(code, self.t, body), expected)

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
        expected = OutputRequest(t, OutputType.Screen, [None], [Screen(buff=buff)])
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)

        code = 0x42 # ScreenTile
        body = bytes([0,0] + [255]*8) # Light up entire left tile
        buff[:,0:8] = 1
        expected = OutputRequest(t, OutputType.Screen, [None], [Screen(buff=buff)])
        self.assertEqual(self.sc.bytes_to_request(code, t, body), expected)


    def test_response_to_bytes(self):
        resp = AckResponse(complete=False)
        expected = 0x80, bytes()
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = AckResponse(complete=True)
        expected = 0x81, bytes()
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = ErrorResponse(complete=False)
        expected = 0x82, bytes()
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = ErrorResponse(complete=True)
        expected = 0x83, bytes()
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = ValuesResponse(values=[1,0,1], analog=False, complete=False)
        expected = 0x80, bytes([1,0,1])
        self.assertEqual(self.sc.response_to_bytes(resp), expected)

        resp = ValuesResponse(values=[-2,-1,65535], analog=True, complete=True)
        expected = 0x81, bytes([254, 255, 255, 255, 255, 255, 255, 255, 255, 255, 0, 0])
        self.assertEqual(self.sc.response_to_bytes(resp), expected)
