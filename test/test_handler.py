from src.handler import *
import unittest

from src.condition import Condition
from src.condition import ConditionType
from src.frame import Frame
from src.request import InputRequest
from src.request import InputType
from src.request import OutputRequest
from src.request import OutputType
from src.response import AckResponse
from src.response import ErrorResponse
from src.response import ValuesResponse
from src.sequence import Sequence
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

        self.handler = RequestHandler(end_condition, frames, preempt=True)
        self.a_params = AnalogParams(-128, 127, 0.0, 5.0)

    def test_update(self):
        request = OutputRequest(0, OutputType.DigitalWrite, [13], [1])
        expected = AckResponse(complete=False)
        self.assertEqual(self.handler.update(request), expected)

        request = InputRequest(50, InputType.AnalogRead, [0], analog_params=self.a_params)
        expected = ErrorResponse(complete=False) # No frame active yet
        self.assertEqual(self.handler.update(request), expected)

        request = InputRequest(150, InputType.AnalogRead, [0], analog_params=self.a_params)
        expected = ValuesResponse(values=[-128], analog=True, complete=False)
        self.assertEqual(self.handler.update(request), expected)

        request = InputRequest(150, InputType.AnalogRead, [1], analog_params=self.a_params)
        expected = ErrorResponse(complete=False) # No data for that channel
        self.assertEqual(self.handler.update(request), expected) 

        request = InputRequest(2150, InputType.AnalogRead, [0], analog_params=self.a_params)
        expected = ErrorResponse(complete=True)
        self.assertEqual(self.handler.update(request), expected)

    def test_get_current_frame_id(self):
        request = InputRequest(150, InputType.AnalogRead, [0], analog_params=self.a_params)
        self.handler.update(request)
        self.assertEqual(self.handler.get_current_frame_id(), 0)

        request = InputRequest(250, InputType.AnalogRead, [0], analog_params=self.a_params)
        self.handler.update(request)
        self.assertEqual(self.handler.get_current_frame_id(), 1)

        self.handler.preempt = False     
        request = InputRequest(250, InputType.AnalogRead, [0], analog_params=self.a_params)
        self.handler.update(request)
        self.assertEqual(self.handler.get_current_frame_id(), 0)

        request = InputRequest(350, InputType.AnalogRead, [0], analog_params=self.a_params)
        self.handler.update(request)
        self.assertEqual(self.handler.get_current_frame_id(), 2)

        request = InputRequest(1050, InputType.AnalogRead, [0], analog_params=self.a_params)
        self.handler.update(request)
        self.assertEqual(self.handler.get_current_frame_id(), 0)

        request = InputRequest(1250, InputType.AnalogRead, [0], analog_params=self.a_params)
        self.handler.update(request)
        self.assertIsNone(self.handler.get_current_frame_id())
