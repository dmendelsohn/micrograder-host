from src.condition import *

from src.request import EventRequest
from src.request import EventType

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