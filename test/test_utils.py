import unittest
import numpy as np
import operator

from src.utils import *

class TestUtils(unittest.TestCase):

    def test_get_default(self):
        # Test the generic function
        defaults = {
            None: 1,
            InputType.DigitalRead: 0,
            (InputType.DigitalRead, 0): 1, # Different default for specific channel
        }
        self.assertEqual(get_default(InputType.DigitalRead, 0, defaults), 1)
        self.assertEqual(get_default(InputType.DigitalRead, 1, defaults), 0)
        self.assertEqual(get_default(InputType.DigitalRead, None, defaults), 0)
        self.assertEqual(get_default(InputType.AnalogRead, 0, defaults), 1)


        del defaults[None]
        self.assertIsNone(get_default(InputType.AnalogRead, 0, defaults))
        

        # Now test the particular functionss
        self.assertEqual(get_default_value(InputType.Accelerometer, 'x'), 0.0)
        self.assertEqual(get_default_value(InputType.Accelerometer), 0.0)
        self.assertEqual(get_default_value(InputType.Accelerometer, 'z'), 1.0)
        self.assertEqual(get_default_check_function(OutputType.DigitalWrite), operator.__eq__)
        self.assertEqual(get_default_aggregator(OutputType.DigitalWrite), all)

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

    def test_decode_analog_params(self):
        b = bytes([254, 255, 255, 255,
                   255, 255, 255, 255,
                   0, 0, 0, 0,
                   1, 0, 0, 0])
        expected = AnalogParams(min_bin=-2, max_bin=-1, min_value=0, max_value=1)
        self.assertEqual(decode_analog_params(b), expected)

    def test_decode_batch_params(self):
        b = bytes([2, 1, 1, 1, 0, 0])
        expected = BatchParams(num=258, period=0.257)
        self.assertEqual(decode_batch_params(b), expected)

    def test_decode_screen_tile(self):
        b = bytes([1, 1, 1, 1, 1, 1, 1, 255]) # Just left and bottom edges of tile
        expected = np.zeros((8,8))
        expected[:,0] = 1 # Left edge
        expected[7,:] = 1 # Bottom edge
        self.assertTrue(np.array_equal(decode_screen_tile(b), expected))
