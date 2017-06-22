from src.case import *
import operator
import unittest

from src import utils
from src.frame import Condition
from src.frame import ConditionType
from src.frame import Frame
from src.request import InputRequest
from src.request import InputType
from src.request import OutputRequest
from src.request import OutputType
from src.response import AckResponse
from src.response import ErrorResponse
from src.response import ValuesResponse
from src.sequence import Sequence
from src.screen import Screen
from src.utils import AnalogParams

class TestTestCase(unittest.TestCase): # This unittest.TestCase is testing the TestCase class
    def setUp(self):
        end_condition = Condition(ConditionType.After, cause=2000)

        frame0 = Frame(
            start_condition=Condition(ConditionType.After, cause=100),
            end_condition=Condition(ConditionType.After, cause=1200),
            inputs={(InputType.AnalogRead, 0): Sequence([0.0],[0])},
            priority=0)
        frame1 = Frame(
            start_condition=Condition(ConditionType.After, cause=200),
            end_condition=Condition(ConditionType.After, cause=1100),
            inputs={(InputType.AnalogRead, 0): Sequence([1.0],[0])},
            priority=0)
        frame2 = Frame(
            start_condition=Condition(ConditionType.After, cause=300),
            end_condition=Condition(ConditionType.After, cause=1000),
            inputs={(InputType.AnalogRead, 0): Sequence([2.0],[0])},
            priority=1)
        frames = [frame0, frame1, frame2]

        tp0 = TestPoint(frame_id=0,
                       output_type=OutputType.DigitalWrite,
                       channel=13,
                       expected_value=1,
                       check_interval=(0,100),
                       check_function=operator.eq,
                       aggregator=lambda x: False) # always False
        tp1 = TestPoint(frame_id=0,
                       output_type=OutputType.DigitalWrite,
                       channel=13,
                       expected_value=1,
                       check_interval=(0,100),
                       check_function=operator.eq,
                       aggregator=lambda x: True) # always True
        tp2 = TestPoint(frame_id=0,
                       output_type=OutputType.DigitalWrite,
                       channel=14,
                       expected_value=1,
                       check_interval=(0,100),
                       check_function=operator.eq,
                       aggregator=lambda x: True) # always True
        test_points = [tp0, tp1, tp2]

        aggregators = {
            (OutputType.DigitalWrite, 13): all
        }

        self.case = TestCase(end_condition, frames, test_points, aggregators, True)
        self.params = AnalogParams(-128, 127, 0.0, 5.0)

    def test_update(self):
        request = OutputRequest(0, OutputType.DigitalWrite, [13], [1])
        expected = AckResponse(test_complete=False)
        self.assertEqual(self.case.update(request), expected)

        request = InputRequest(50, InputType.AnalogRead, [0], analog_params=self.params)
        expected = ErrorResponse(test_complete=False) # No frame active yet
        self.assertEqual(self.case.update(request), expected)

        request = InputRequest(150, InputType.AnalogRead, [0], analog_params=self.params)
        expected = ValuesResponse(values=[-128], analog=True, test_complete=False)
        self.assertEqual(self.case.update(request), expected)

        request = InputRequest(150, InputType.AnalogRead, [1], analog_params=self.params)
        expected = ErrorResponse(test_complete=False) # No data for that channel
        self.assertEqual(self.case.update(request), expected)

        req = InputRequest(150, InputType.AnalogRead, [1], values=[0], analog_params=self.params)
        expected = ErrorResponse(test_complete=False) # No "input recordings" during live test
        self.assertEqual(self.case.update(req), expected)        

        request = InputRequest(2150, InputType.AnalogRead, [0], analog_params=self.params)
        expected = ErrorResponse(test_complete=True)
        self.assertEqual(self.case.update(request), expected)

        expected_output_log = OutputLog()
        expected_output_log.record_output(OutputType.DigitalWrite, 13, 0, 1)
        self.assertEqual(self.case.output_log, expected_output_log)

    def test_get_current_frame_id(self):
        request = InputRequest(150, InputType.AnalogRead, [0], analog_params=self.params)
        self.case.update(request)
        self.assertEqual(self.case.get_current_frame_id(), 0)

        request = InputRequest(250, InputType.AnalogRead, [0], analog_params=self.params)
        self.case.update(request)
        self.assertEqual(self.case.get_current_frame_id(), 1)

        self.case.preempt = False     
        request = InputRequest(250, InputType.AnalogRead, [0], analog_params=self.params)
        self.case.update(request)
        self.assertEqual(self.case.get_current_frame_id(), 0)

        request = InputRequest(350, InputType.AnalogRead, [0], analog_params=self.params)
        self.case.update(request)
        self.assertEqual(self.case.get_current_frame_id(), 2)

        request = InputRequest(1050, InputType.AnalogRead, [0], analog_params=self.params)
        self.case.update(request)
        self.assertEqual(self.case.get_current_frame_id(), 0)

        request = InputRequest(1250, InputType.AnalogRead, [0], analog_params=self.params)
        self.case.update(request)
        self.assertIsNone(self.case.get_current_frame_id())

    def test_assess(self):
        self.case.output_log.record_frame_start(0, 1000)

        expected = {
            (OutputType.DigitalWrite, 13): False,
            (OutputType.DigitalWrite, 14): False
        }
        self.assertEqual(self.case.assess(), expected)

        self.case.aggregators[(OutputType.DigitalWrite, 13)] = any
        expected[(OutputType.DigitalWrite, 13)] = True
        self.assertEqual(self.case.assess(), expected)


    def test_assess_test_point(self):
        tp = TestPoint(frame_id=0,
                       output_type=OutputType.DigitalWrite,
                       channel=13,
                       expected_value=1,
                       check_interval=(0,100),
                       check_function=operator.eq,
                       aggregator=all)

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
