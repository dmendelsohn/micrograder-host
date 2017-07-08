from src.sequence import *
import unittest

class TestSequence(unittest.TestCase):
    def setUp(self):
        times = [0, 10, 20, 30]
        values = [10, 8.5, "foo", []] # Values can be pretty much anything
        self.seq = Sequence(times, values)

    def test_basic_functions(self):
        self.assertEqual(self.seq[0], (0,10))
        self.assertEqual(self.seq[0].time, 0) # Test .time access
        self.assertEqual(self.seq[0].value, 10) # Test .value access
        self.assertEqual(self.seq[1], (10, 8.5))
        self.assertEqual(self.seq[2], (20, "foo"))
        self.assertEqual(self.seq[3], (30, []))
        self.assertEqual(len(self.seq), 4)

        points = self.seq[0:3:2]
        self.assertEqual(len(points), 2)
        self.assertEqual(points[0], (0,10))
        self.assertEqual(points[1], (20, "foo"))

        # Append a new element
        self.seq.append(40, None)
        self.assertEqual(self.seq[4], (40, None))
        self.assertEqual(len(self.seq), 5)

        # Insert an element
        seq = self.seq.insert(5, 0)
        self.assertEqual(seq, self.seq)
        self.assertEqual(self.seq[1], (5, 0))

    def test_shift(self):
        seq = self.seq.shift(1)
        self.assertEqual(seq, self.seq)
        self.assertEqual(self.seq, Sequence(times=[1,11,21,31],values=[10,8.5,"foo",[]]))


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

    def test_get_subsequence(self):
        original_seq = self.seq.copy()

        subseq = self.seq.get_subsequence(0,10)
        self.assertEqual(subseq, Sequence(times=[0], values=[10]))

        subseq = self.seq.get_subsequence(1,11)
        self.assertEqual(subseq, Sequence(times=[10], values=[8.5]))

        subseq = self.seq.get_subsequence(-1, 1)
        self.assertEqual(subseq, Sequence(times=[0], values=[10]))

        subseq = self.seq.get_subsequence(0,0)
        self.assertEqual(subseq, Sequence())

        self.assertEqual(self.seq, original_seq) # Ensure the original is unmodified

    def test_remove_duplicates(self):
        seq = Sequence(times=[0,1,2,3,4], values=[10,10,11,10,10])
        seq2 = seq.remove_duplicates()
        self.assertEqual(seq, seq2)
        self.assertEqual(seq, Sequence(times=[0,2,3], values=[10,11,10]))

    def test_interpolate(self):
        seq = Sequence(times=[0,5,9], values=[0, 1, 2])

        seq1 = seq.interpolate(InterpolationType.Start)
        self.assertEqual(seq1, Sequence(times=[0,5,9], values=[0, 1, 2]))

        seq2 = seq.interpolate(InterpolationType.End)
        self.assertEqual(seq2, Sequence(times=[0,5], values=[1, 2]))

        seq3 = seq.interpolate(InterpolationType.Mid)
        self.assertEqual(seq3, Sequence(times=[0,2,7], values=[0,1,2]))

        seq4 = seq.interpolate(InterpolationType.Linear, res=2)
        self.assertEqual(seq4, Sequence(times=[0,2,4,5,7,9], values=[0, 0.4, 0.8, 1, 1.5, 2]))
