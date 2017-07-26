from src.frame import *

from src.condition import Condition
from src.condition import ConditionType
from src.request import EventRequest
from src.request import InputRequest
from src.response import ErrorResponse
from src.response import ValuesResponse
from src.sequence import Sequence
from src.utils import AnalogParams
from src.utils import BatchParams
from src.utils import EventType
from src.utils import InputType

import unittest

def request_is_init(request):
    return request.data_type == EventType.Init

def request_is_print(request):
    return request.data_type == EventType.Print

class TestFrame(unittest.TestCase):
    def setUp(self):
        start = Condition(ConditionType.After, cause=request_is_init)
        end = Condition(ConditionType.After, cause=request_is_print)
        seq0 = Sequence(times=[100], values=[1.0])
        seq1 = Sequence(times=[110], values=[2.0])
        inputs = {(InputType.AnalogRead, 0): seq0, (InputType.AnalogRead, 1): seq1}
        self.frame = Frame(start, end, inputs)

    def test_status(self):
        self.assertEqual(self.frame.status, FrameStatus.NotBegun)
        self.frame.update(EventRequest(50, EventType.Init))
        self.assertEqual(self.frame.status, FrameStatus.InProgress)
        self.frame.update(EventRequest(1050, EventType.Print))
        self.assertEqual(self.frame.status, FrameStatus.Complete)

    def test_avoided(self):
        self.assertEqual(self.frame.status, FrameStatus.NotBegun)
        self.frame.update(EventRequest(1050, EventType.Print))
        self.assertEqual(self.frame.status, FrameStatus.Avoided)

    def test_values(self):
        params = AnalogParams(-128, 127, 0.0, 5.0)
        input_type = InputType.AnalogRead

        request = InputRequest(25, input_type, [0,1], analog_params=params)
        actual = self.frame.get_response(request)
        self.assertEqual(actual, ErrorResponse()) # Error, frame hasn't started

        self.frame.update(EventRequest(50, EventType.Init)) # Starts the frame

        request = InputRequest(159, input_type, [0,1], analog_params=params)
        actual = self.frame.get_response(request)
        self.assertEqual(actual, ErrorResponse()) # Error, one channel doesn't have data yet

        request = InputRequest(160, input_type, [0,2], analog_params=params)
        actual = self.frame.get_response(request)
        self.assertEqual(actual, ErrorResponse()) # Error, one channel is invalid

        request = InputRequest(160, input_type, [0,1], analog_params=params)
        actual = self.frame.get_response(request)
        self.assertEqual(actual, ValuesResponse(values=[-77, -26], analog=True))  # Success

        b_params = BatchParams(num=2, period=10)
        request = InputRequest(160, input_type, [0,1], analog_params=params, batch_params=b_params)
        actual = self.frame.get_response(request)
        self.assertEqual(actual, ValuesResponse(values=[-77, -26, -77, -26], analog=True))

        self.frame.update(EventRequest(1000, EventType.Print)) # Ends the frame
        actual = self.frame.get_response(InputRequest(1000, input_type, [0,1], analog_params=params))
        self.assertEqual(actual, ErrorResponse())  # Frame has completed
