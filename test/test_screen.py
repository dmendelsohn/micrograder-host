from src.screen import *
import unittest
import numpy as np

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

    # Later: tests for more sophisticated screen methods

