from src.frame import *
from src.request import EventRequest
from src.request import EventType
from src.request import InputRequest
from src.request import InputType
from src.response import ErrorResponse
from src.response import ValuesResponse
from src.sequence import Sequence
from src.utils import AnalogParams
from src.utils import BatchParams
import unittest

def request_is_init(request):
    return request.is_event and request.data_type == EventType.Init

def request_is_print(request):
    return request.is_event and request.data_type == EventType.Print

class TestCondition(unittest.TestCase):
    def setUp(self):
        cond0 = Condition(ConditionType.After, cause=100)
        cond1 = Condition(ConditionType.After, cause=request_is_init)
        cond2 = Condition(ConditionType.After, cause=request_is_print, subconditions=[cond1])
        cond3 = Condition(ConditionType.Or, subconditions=[cond0, cond1, cond2])
        cond4 = Condition(ConditionType.And, subconditions=[cond0, cond1, cond2, cond3])
        self.conditions = [cond0, cond1, cond2, cond3, cond4]

        req0 = EventRequest(50, EventType.Print) # Satisfied: {none}
        req1 = EventRequest(100, EventType.Init) # Satisfied: {cond0, cond1, cond3}
        req2 = EventRequest(200, EventType.Wifi) # Satisfied: {cond0, cond1, cond3}
        req3 = EventRequest(300, EventType.Print) # Satisfied: {all}
        self.requests = [req0, req1, req2, req3]

    def test_basic_functions(self):
        def satisfied_times():
            return [cond.satisfied_at for cond in self.conditions]

        self.assertIsNone(self.conditions[4].last_update_request)

        self.conditions[4].update(self.requests[0])
        self.assertEqual(satisfied_times(), [None, None, None, None, None])

        self.conditions[4].update(self.requests[1])
        self.assertEqual(satisfied_times(), [100, 100, None, 100, None])

        self.conditions[4].update(self.requests[2])
        self.assertEqual(satisfied_times(), [100, 100, None, 100, None])

        self.conditions[4].update(self.requests[3])
        self.assertEqual(satisfied_times(), [100, 100, 300, 100, 300])

        self.assertEqual(self.conditions[4].last_update_request, self.requests[3])  

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
