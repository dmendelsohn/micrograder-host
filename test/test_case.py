from src.case import *
import unittest

from src.condition import Condition
from src.condition import ConditionType
from src.log import RequestLog
from src.request import EventRequest
from src.request import EventType
from src.request import InputRequest
from src.request import InputType
from src.request import OutputRequest
from src.request import OutputType
from src.screen import Screen
from src.sequence import InterpolationType
from src.sequence import Sequence

import numpy as np
import operator

class ScaffoldTest(unittest.TestCase):
    def setUp(self):
        def is_start_request(request):
            return (request.data_type == EventType.Print and request.arg == "Start")
        start_cond = Condition(ConditionType.After, cause=is_start_request)
        end_cond = Condition(ConditionType.After, cause=5000, subconditions=[start_cond])
        ft0 = FrameTemplate(start_condition=start_cond,
                            end_condition=end_cond,
                            priority=0,
                            init_to_default=True
            )
        frame_templates = [ft0]
        interpolations = {(InputType.DigitalRead, 6): InterpolationType.START}
        defaults = {(InputType.DigitalRead, 6): 1}

        pt0 = TestPointTemplate(check_interval=("0.2*T", "0.8*T"),
                                check_function=operator.__eq__,
                                aggregator=all)
        point_templates = {(OutputType.DigitalWrite, 13): pt0,
                           (OutputType.Screen, None): pt0}
        aggregators = {(OutputType.DigitalWrite, 13): all,
                       (OutputType.Screen, None): all}
        self.scaffold = Scaffold(frame_templates=frame_templates,
                                 interpolations=interpolations,
                                 defaults=defaults,
                                 point_templates=point_templates,
                                 aggregators=aggregators)

        # Now create a button-test log
        requests = []
        requests.append(EventRequest(timestamp=900, data_type=EventType.Init))
        requests.append(EventRequest(timestamp=1000, data_type=EventType.Print, arg="Start"))

        dread = [1]*20 + [0]*40 + [1]*10 + [0]*10 + [1]*30 # OFF,ON,OFF,ON,OFF
        for i in range(len(dread)):  # Add input/outputs for each loop
            requests.append(InputRequest(timestamp=(1000+50*i+1),
                                         data_type=InputType.DigitalRead,
                                         channels=[6],
                                         values=[dread[i]]))

            requests.append(OutputRequest(timestamp=(1000+50*i+2),
                                          data_type=OutputType.DigitalWrite,
                                          channels=[13],
                                          values=[1-dread[i]]))

            screen = Screen(width=128, height=64)
            if dread[i]==0:
                screen.paint(np.ones((10,20)), x=20, y=10)
            requests.append(OutputRequest(timestamp=(1000+50*i+2),
                                          data_type=OutputType.Screen,
                                          channels=[None],
                                          values=[screen]))

        requests.sort(key=lambda request: request.timestamp)
        self.log = RequestLog()
        for request in requests:
            self.log.update(request)

    def test_generate_case(self):
        #TODO: test
        pass


    def test_generate_frame_bounds(self):
        ft1 = self.scaffold.frame_templates[0]

        expected = (1000, 6000)
        actual = self.scaffold.generate_frame_bounds(self.log, ft1)
        self.assertEqual(expected, actual)

        always = Condition(ConditionType.After, cause=lambda req: True)
        never = Condition(ConditionType.After, cause=lambda req: False)

        ft2 = FrameTemplate(start_condition=ft1.start_condition,
                            end_condition=always,
                            priority=0,
                            init_to_default=True)
        actual = self.scaffold.generate_frame_bounds(self.log, ft2)
        self.assertIsNone(actual) # Because end is before start

        ft3 = FrameTemplate(start_condition=ft1.start_condition,
                            end_condition=never,
                            priority=0,
                            init_to_default=True)
        actual = self.scaffold.generate_frame_bounds(self.log, ft3)
        self.assertIsNone(actual) # Because end_condition never occurs

    def test_generate_inputs(self):
        overall_sequences = self.log.extract_sequences()

        # Test that default gets used when there is no lead-in value
        start_time = 1000
        end_time = 6000
        init_to_default = False
        values = [1] + [1]*20 + [0]*40 + [1]*10 + [0]*10 + [1]*30 # OFF,ON,OFF,ON,OFF
        times = [0] + list(range(1, end_time - start_time, 50))
        seq = Sequence(times=times, values=values[:len(times)])
        expected = {(InputType.DigitalRead, 6): seq}
        actual = self.scaffold.generate_inputs(overall_sequences, start_time,
                                               end_time, init_to_default)
        self.assertEqual(actual, expected)

        # Test that additional value isn't added if input at exactly start_time
        start_time = 1001
        end_time = 6000
        init_to_default = False
        values = [1]*20 + [0]*40 + [1]*10 + [0]*10 + [1]*30 # OFF,ON,OFF,ON,OFF
        times = list(range(0, end_time - start_time, 50))
        seq = Sequence(times=times, values=values[:len(times)])
        expected = {(InputType.DigitalRead, 6): seq}
        actual = self.scaffold.generate_inputs(overall_sequences, start_time,
                                               end_time, init_to_default)
        self.assertEqual(actual, expected)

        # Test that non-default "lead in" values work
        start_time = 3000
        end_time = 6000
        init_to_default = False
        values = [0] + [0]*20 + [1]*10 + [0]*10 + [1]*30 # OFF,ON,OFF,ON,OFF
        times = [0] + list(range(1, end_time - start_time, 50))
        seq = Sequence(times=times, values=values[:len(times)])
        expected = {(InputType.DigitalRead, 6): seq}
        actual = self.scaffold.generate_inputs(overall_sequences, start_time,
                                               end_time, init_to_default)
        self.assertEqual(actual, expected)        

        # Test that init_to_default flag actually does something
        start_time = 3000
        end_time = 6000
        init_to_default = True
        values = [1] + [0]*20 + [1]*10 + [0]*10 + [1]*30 # OFF,ON,OFF,ON,OFF
        times = [0] + list(range(1, end_time - start_time, 50))
        seq = Sequence(times=times, values=values[:len(times)])
        expected = {(InputType.DigitalRead, 6): seq}
        actual = self.scaffold.generate_inputs(overall_sequences, start_time,
                                               end_time, init_to_default)
        self.assertEqual(actual, expected) 

        # Test that no values in range still produces a singleton sequence
        start_time = 0
        end_time = 100
        init_to_default = False
        expected = {(InputType.DigitalRead, 6): Sequence(times=[0], values=[1])}
        actual = self.scaffold.generate_inputs(overall_sequences, start_time,
                                               end_time, init_to_default)
        self.assertEqual(actual, expected)

         # Test that linear interpolation usage
        self.scaffold.interpolations[(InputType.DigitalRead, 6)] = InterpolationType.LINEAR
        start_time = 1001
        end_time = 6000
        init_to_default = False
        values = [1]*20 + [0]*40 + [1]*10 + [0]*10 + [1]*30 # OFF,ON,OFF,ON,OFF
        times = list(range(0, end_time - start_time, 50))
        seq = Sequence(times=times, values=values[:len(times)])
        seq = seq.interpolate(InterpolationType.LINEAR, res=utils.MILLISECOND)
        expected = {(InputType.DigitalRead, 6): seq}
        actual = self.scaffold.generate_inputs(overall_sequences, start_time,
                                               end_time, init_to_default)
        self.assertEqual(actual, expected)       

    def test_generate_test_points(self):
        #TODO: implement
        pass