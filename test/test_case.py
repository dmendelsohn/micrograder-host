from src.case import *
import operator
import unittest

from src import utils
from src.request import OutputType
from src.sequence import Sequence
from src.screen import Screen

class TestTestCase(unittest.TestCase): # This unittest.TestCase is testing the TestCase class
    def setUp(self):
        #TODO: implement
        pass

    def test_update(self):
        #TODO: implement
        pass

    def test_get_current_frame_id(self):
        #TODO: implement
        pass

    def test_assess(self):
        #TODO: implement
        pass

    def test_assess_test_point(self):
        tp = TestPoint(frame_id=0,
                       output_type=OutputType.DigitalWrite,
                       channel=13,
                       expected_value=1,
                       check_interval=(0,100),
                       check_function=operator.eq,
                       aggregator=utils.AND)

        output_log = OutputLog()

        seq = Sequence([900, 1000, 1050, 1100], [0, 1, 1, 0])
        output_log.outputs[(OutputType.DigitalWrite, 13)] = seq
        self.assertFalse(assess_test_point(tp, output_log)) # No frame

        output_log.record_frame_start(frame_id=0,  start_time=1000)
        self.assertTrue(assess_test_point(tp, output_log))

        seq = Sequence([900, 1001, 1050, 1100], [0, 1, 1, 0])
        output_log.outputs[(OutputType.DigitalWrite, 13)] = seq
        self.assertFalse(assess_test_point(tp, output_log))

        seq = Sequence([900, 1000, 1050, 1099], [0, 1, 1, 0])
        output_log.outputs[(OutputType.DigitalWrite, 13)] = seq
        self.assertFalse(assess_test_point(tp, output_log))

        seq = Sequence([900, 1000, 1050], [0, 1, 1])
        output_log.outputs[(OutputType.DigitalWrite, 13)] = seq
        self.assertTrue(assess_test_point(tp, output_log))

        seq = Sequence([1050], [1])
        output_log.outputs[(OutputType.DigitalWrite, 13)] = seq
        self.assertFalse(assess_test_point(tp, output_log)) # Starts undefined

        seq = Sequence()
        output_log.outputs[(OutputType.DigitalWrite, 13)] = seq
        self.assertFalse(assess_test_point(tp, output_log)) # Always undefined

        del output_log.outputs[(OutputType.DigitalWrite, 13)]
        self.assertFalse(assess_test_point(tp, output_log)) # No key in dict

class TestOutputLog(unittest.TestCase):
    
    def test_basic_functions(self):
        output_log = OutputLog()
        output_log.record_output(OutputType.DigitalWrite, 13, 100, 1)
        output_log.record_output(OutputType.DigitalWrite, 13, 200, 0)
        output_log.record_output(OutputType.AnalogWrite, 0, 300, 1.5)
        output_log.record_output(OutputType.Screen, None, 400, Screen(width=128, height=64))
        output_log.record_frame_start(0, 50)

        expected_log = OutputLog()
        seq0 = Sequence(times=[100, 200], values=[1,0])
        seq1 = Sequence(times=[300], values=[1.5])
        seq2 = Sequence(times=[400], values=[Screen(width=128, height=64)])
        expected_log.outputs = {
            (OutputType.DigitalWrite, 13): seq0,
            (OutputType.AnalogWrite, 0): seq1,
            (OutputType.Screen, None): seq2
        }
        expected_log.frame_start_times = {0: 50}

        self.assertEqual(output_log, expected_log)
