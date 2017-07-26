from src.screen import *
import unittest
import numpy as np

from src import utils

class TestScreen(unittest.TestCase):
    def test_basic_functions(self):
        screen1 = Screen(width=128, height=64)
        self.assertEqual(screen1.height(), 64)
        self.assertEqual(screen1.width(), 128)

        screen2 = Screen(width=128, height=64)
        self.assertEqual(screen1, screen2) # Test __eq__

        screen3 = screen2.copy()
        screen3.buffer[0,0] = 1
        self.assertNotEqual(screen2, screen3)

        rect = np.ones((1,1))
        screen2.paint(rect, x=0, y=0)
        self.assertEqual(screen2, screen3)

        expected = np.zeros((3,2))
        expected[0,0] = 1
        self.assertTrue(np.array_equal(screen2.get_box(0,0,2,3), expected))

    def test_get_box_values(self):
        screen = Screen(width=4, height=3)
        rect = np.ones((2,2))
        screen.paint(rect, x=0, y=0)
        box_width = 3
        box_height = 2

        expected = [
            [60, 48, 0, 0],
            [40, 32, 0, 0],
            [0, 0, 0, 0]
        ]
        actual = screen.get_box_values(box_width, box_height)
        self.assertEqual(actual, expected)

    def test_extract_text(self):
        screen = utils.load('test/resources/screens/multiline_text')
        font = utils.load('test/resources/fonts/u8g2_5x7')
        actual = screen.extract_text(font)
        expected = "This is a multiline stri\nng"
        self.assertEqual(actual, expected)

    def test_get_num_matching_pixels(self):
        buffer1 = np.zeros((3,3), dtype=np.uint8)
        buffer1[0:2,0:2] = 1
        screen1 = Screen(buff=buffer1)
        buffer2 = np.zeros((3,3), dtype=np.uint8)
        buffer2[1:3,1:3] = 1
        screen2 = Screen(buff=buffer2)
        screen3 = Screen(width=4, height=4)

        # Without shifts
        self.assertEqual(screen1.get_num_matching_pixels(screen2), 3)

        # Test that up and left shifts work
        self.assertEqual(screen1.get_num_matching_pixels(screen2, up=1), 5)
        self.assertEqual(screen1.get_num_matching_pixels(screen2, left=1), 5)
        self.assertEqual(screen1.get_num_matching_pixels(screen2, up=1, left=1), 9)

        # Test that down and right shifts work
        self.assertEqual(screen2.get_num_matching_pixels(screen1, down=1), 5)
        self.assertEqual(screen2.get_num_matching_pixels(screen1, right=1), 5)
        self.assertEqual(screen2.get_num_matching_pixels(screen1, down=1, right=1), 9)

        # Test that catch-all "shift" keyword works
        self.assertEqual(screen1.get_num_matching_pixels(screen2, shift=1), 9)

        # Test that non-matching shapes are discarded
        with self.assertRaises(ValueError):
            screen2.get_num_matching_pixels(screen3)


    def test_check_functions(self):
        screen_i = Screen(buff=np.eye(3, dtype=np.uint8))
        screen_on = Screen(buff=np.ones((3,3), dtype=np.uint8))
        screen_off = Screen(buff=np.zeros((3,3), dtype=np.uint8))
        f3 = pixel_match_min(3)
        f4 = pixel_match_min(4)
        e5 = pixel_error_max(5)
        e6 = pixel_error_max(6)

        self.assertTrue(f3(screen_i, screen_on))
        self.assertFalse(f4(screen_i, screen_on))
        self.assertFalse(e5(screen_i, screen_on))
        self.assertTrue(e6(screen_i, screen_on))

        # Now test the more complicated relatively_close funtion
        r00 = relatively_close(0.0) # Off screen is considered correct
        r30 = relatively_close(0.30)
        r35 = relatively_close(0.35)
        r100 = relatively_close(1.00) # Equivalent to op.__eq__

        self.assertTrue(r00(screen_on, screen_off))
        self.assertFalse(r30(screen_on, screen_off))
        self.assertTrue(r30(screen_on, screen_i)) # 3 out of 9 pixels is enough...
        self.assertFalse(r35(screen_on, screen_i)) # ...Not anymore
        self.assertTrue(r100(screen_on, screen_on))


