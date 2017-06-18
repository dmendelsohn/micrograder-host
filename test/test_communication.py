from src.communication import *
from src.utils import AnalogParams
import unittest

class TestSerialCommunication(unittest.TestCase):
    def setUp(self):
        self.sc = SerialCommunication()

    def test_response_to_bytes(self):
        #TODO: implement
        pass

    def test_bytes_to_request(self):  # Except for screen output requests
        #TODO: implement
        pass

    def test_bytes_to_screen_request(self):
        #TODO: implement
        pass