from src.case import *
import unittest

from src.request import OutputType
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
        #TODO: impelement
        pass

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
