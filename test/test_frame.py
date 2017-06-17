from src.frame import *
from src.request import EventRequest
from src.request import EventType
import unittest

class TestCondition(unittest.TestCase):
    def setUp(self):
        def request_is_init(request):
            return request.is_event and request.data_type == EventType.Init

        def request_is_print(request):
            return request.is_event and request.data_type == EventType.Print

        cond0 = Condition(ConditionType.AFTER, cause=100)
        cond1 = Condition(ConditionType.AFTER, cause=request_is_init)
        cond2 = Condition(ConditionType.AFTER, cause=request_is_print, subconditions=[cond1])
        cond3 = Condition(ConditionType.OR, subconditions=[cond0, cond1, cond2])
        cond4 = Condition(ConditionType.AND, subconditions=[cond0, cond1, cond2, cond3])
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
        #self.frame = ?? # TODO
        pass

    def test_status(self):
        # TODO: start and end the frame, testing status along the way
        pass

    def test_avoided(self):
        # TODO: end the frame, testing status along the way
        pass

    def test_values(self):
        # TODO: test some values, including before, during, after satisfaction
        # TDOO: also include test where frame is satisfied, but value is undefined
        pass