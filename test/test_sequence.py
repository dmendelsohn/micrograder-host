from src.sequence import *
import unittest

class TestSequence(unittest.TestCase):
    def setUp(self):
        times = [0, 10, 20, 30]
        values = [10, 8.5, "foo", []] # Values can be pretty much anything
        self.seq = ValueSequence(times, values)

    def test_basic_functions(self):
        self.assertEqual(self.seq[0], (0,10))
        self.assertEqual(self.seq[1], (10, 8.5))
        self.assertEqual(self.seq[2], (20, "foo"))
        self.assertEqual(self.seq[3], (30, []))
        self.assertEqual(len(self.seq), 4)

        # Append a new element
        self.seq.append(40, None)
        self.assertEqual(self.seq[4], (40, None))
        self.assertEqual(len(self.seq), 5)


    def test_get_value(self):
        #TODO
        pass

    def test_get_values(self):
        #TODO
        pass

