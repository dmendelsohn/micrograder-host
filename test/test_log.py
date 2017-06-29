from src.log import *
import unittest

from src.condition import Condition
from src.condition import ConditionType
from src.request import EventRequest
from src.request import EventType
from src.request import InputRequest
from src.request import InputType
from src.request import OutputRequest
from src.request import OutputType
from src.screen import Screen
from src.sequence import Sequence
from src.utils import AnalogParams
from src.utils import BatchParams

class TestRequestLog(unittest.TestCase):
    def setUp(self):
        a_params = AnalogParams(-128, 127, 0.0, 5.0)
        b_params = BatchParams(num=2, period=10)

        self.log = RequestLog()
        req0 = OutputRequest(timestamp=100, data_type=OutputType.DigitalWrite,
                             channels=[13], values=[1])
        req1 = OutputRequest(timestamp=200, data_type=OutputType.DigitalWrite,
                             channels=[12,13], values=[1,0])
        req2 = OutputRequest(timestamp=300, data_type=OutputType.AnalogWrite,
                             channels=[0], values=[127], analog_params=a_params)
        req3 = OutputRequest(timestamp=400, data_type=OutputType.Screen,
                             channels=[None], values=[Screen(width=128, height=64)])
        req4 = InputRequest(timestamp=500, data_type=InputType.DigitalRead,
                            channels=[5,6], batch_params=b_params)
        req5 = InputRequest(timestamp=600, data_type=InputType.DigitalRead,
                            channels=[5,6], values=[0,1,0,1], batch_params=b_params)
        req6 = EventRequest(timestamp=700, data_type=EventType.Print, arg="foo")
        for request in [req0, req1, req2, req3, req4, req5, req6]:
            self.log.update(request)
    
    def test_extract_sequences(self):
        seq0 = Sequence(times=[100, 200], values=[1,0])
        seq1 = Sequence(times=[300], values=[5.0])
        seq2 = Sequence(times=[400], values=[Screen(width=128, height=64)])
        seq3 = Sequence(times=[200], values=[1])
        seq4 = Sequence(times=[500,510,600,610],values=[None,None,0,0])
        seq5 = Sequence(times=[500,510,600,610],values=[None,None,1,1])
        seq6 = Sequence(times=[700], values=["foo"])

        expected_sequences = {
            (OutputType.DigitalWrite, 13): seq0,
            (OutputType.AnalogWrite, 0): seq1,
            (OutputType.Screen, None): seq2,
            (OutputType.DigitalWrite, 12): seq3,
            (InputType.DigitalRead, 5): seq4,
            (InputType.DigitalRead, 6): seq5,
            (EventType.Print, None): seq6
        }
        
        self.assertEqual(self.log.extract_sequences(), expected_sequences)

    def test_condition_satisfied_at(self):
        cond0 = Condition(ConditionType.After, cause=lambda req: req.is_output) # First output
        cond1 = Condition(ConditionType.After, cause=50, subconditions=[cond0]) # 50 time units later
        cond2 = Condition(ConditionType.After, cause=1000) # Shouldn't happen
        
        self.assertEqual(self.log.condition_satisfied_at(cond0), 100)
        self.assertEqual(self.log.condition_satisfied_at(cond1), 150)
        self.assertIsNone(self.log.condition_satisfied_at(cond2))

    def test_get_end_time(self):
        #TODO: write test
        pass

    def test_filter(self):
        #TODO: write test
        pass

