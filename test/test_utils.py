import unittest
from src.utils import *

class TestUtils(unittest.TestCase):

    def test_decode_int(self):
        # 1 byte
        self.assertEqual(decode_int(bytes([1]),signed=False), 1)
        self.assertEqual(decode_int(bytes([254]),signed=True), -2)

        # 2 bytes
        self.assertEqual(decode_int(bytes([1, 0]),signed=False), 1)
        self.assertEqual(decode_int(bytes([254, 255]),signed=True), -2)

        # 4 bytes
        self.assertEqual(decode_int(bytes([1, 0, 0, 0]),signed=False), 1)
        self.assertEqual(decode_int(bytes([254, 255, 255, 255]),signed=True), -2)

        with self.assertRaises(ValueError):
            decode_int(bytes([1, 2, 3]), signed=True)

    def test_encode_int(self):
        # 1 byte
        self.assertEqual(encode_int(1, width=1, signed=False), bytes([1]))
        self.assertEqual(encode_int(-2, width=1, signed=True), bytes([254]))

        # 2 bytes
        self.assertEqual(encode_int(1, width=2, signed=False), bytes([1,0]))
        self.assertEqual(encode_int(-2, width=2, signed=True), bytes([254,255]))

        # 4 bytes
        self.assertEqual(encode_int(1, width=4, signed=False), bytes([1,0,0,0]))
        self.assertEqual(encode_int(-2, width=4, signed=True), bytes([254,255,255,255]))

        with self.assertRaises(ValueError):
            encode_int(0, width=3, signed=True)

    def test_analog_to_digital(self):
        params = AnalogParams(-128, 127, 0.0, 5.0)

        # Typical cases
        self.assertEqual(analog_to_digital(0.0, params), -128)
        self.assertEqual(analog_to_digital(5.0, params), 127)
        self.assertEqual(analog_to_digital(2.5098, params), 0)

        # Bounding
        self.assertEqual(analog_to_digital(-1.0, params), -128)
        self.assertEqual(analog_to_digital(6.0, params), 127)

    def test_digital_to_analog(self):
        params = AnalogParams(-128, 127, 0.0, 5.0)
        
        # Typical cases
        self.assertEqual(digital_to_analog(-128, params), 0.0)
        self.assertEqual(digital_to_analog(127, params), 5.0)
        self.assertAlmostEqual(digital_to_analog(0, params), 2.5098, places=3)

        # Bounding
        self.assertEqual(digital_to_analog(-150, params), 0.0)
        self.assertEqual(digital_to_analog(150, params), 5.0)