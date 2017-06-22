from src.sequence import *
import unittest

class TestSequence(unittest.TestCase):
    def setUp(self):
        times = [0, 10, 20, 30]
        values = [10, 8.5, "foo", []] # Values can be pretty much anything
        self.seq = Sequence(times, values)

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


    def test_get_sample(self):
        self.assertIsNone(self.seq.get_sample(-1))
        self.assertEqual(self.seq.get_sample(0),10)
        self.assertEqual(self.seq.get_sample(5),10)
        self.assertEqual(self.seq.get_sample(100), [])

    def test_get_samples(self):
        self.assertIsNone(self.seq.get_samples(-1, num_samples=5, period=5))
        self.assertEqual(self.seq.get_samples(0, num_samples=1, period=5), [10])
        self.assertEqual(self.seq.get_samples(0, num_samples=3, period=5), [10, 10, 8.5])
        self.assertEqual(self.seq.get_samples(25, num_samples=3, period=5), ["foo", [], []])

    def test_get_values(self):
        self.assertEqual(self.seq.get_values(-1, 0), [None])
        self.assertEqual(self.seq.get_values(-1, 1), [None, 10])
        self.assertEqual(self.seq.get_values(-1, 100), [None, 10, 8.5, "foo", []])

        self.assertEqual(self.seq.get_values(9, 20), [10, 8.5])
        self.assertEqual(self.seq.get_values(10,20), [8.5])

