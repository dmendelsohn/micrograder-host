from src.communication import *
from src.response import AckResponse
from src.response import ErrorResponse
from src.response import ValuesResponse
from src.utils import AnalogParams
import unittest

class TestSerialCommunication(unittest.TestCase):
    def setUp(self):
        self.sc = SerialCommunication()

    def test_bytes_to_request_digital(self):
        #TODO: implement
        pass

    def test_bytes_to_request_analog(self):
        #TODO: implement
        pass

    def test_bytes_to_request_event(self):  # Except for screen output requests
        #TODO: implement
        pass

    def test_bytes_to_screen_screen(self):
        #TODO: implement
        pass

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
