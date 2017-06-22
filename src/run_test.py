from .case import TestCase
from .case import TestPoint
from .communication import SerialCommunication
from .frame import Condition
from .frame import ConditionType
from .frame import Frame
from .request import EventType
from .request import InputType 
from .request import OutputType
from .response import ErrorResponse
from .sequence import Sequence
from .screen import Screen

import numpy as np
import operator

def run_test(test_case):
    sc = SerialCommunication()
    while not sc.connect():
        # Do nothing, wait for connection
        pass

    total_log = []
    print("Starting Test")
    while True:
        request = sc.get_request()
        print(request)
        if request.is_valid:
            response = test_case.update(request)
        else:
            response = ErrorResponse()

        print(response)
        sc.send_response(response)
        total_log.append((request, response))
        if response.is_error or response.test_complete:
            break

    print("Assessing")
    return test_case.assess()

def save_test(test_case, filename):
    #TODO: implement
    pass

def load_test(filename):
    #TODO: implement
    pass

def constant_test_case():
    init_condition = Condition(ConditionType.After, 
                               cause=lambda req: req.data_type == EventType.Init)
    end_condition = Condition(ConditionType.After,
                              cause=3000, subconditions=[init_condition])
    frame = Frame(init_condition, end_condition,
                    inputs={
                        (InputType.DigitalRead, 13): Sequence([0],[1]),
                        (InputType.AnalogRead, 0): Sequence([0],[1650]), # 1.65V
                        (InputType.Accelerometer, 'x'): Sequence([0], [1.5]), # 1.5Gs
                        (InputType.Accelerometer, 'y'): Sequence([0], [1.6]),
                        (InputType.Accelerometer, 'z'): Sequence([0], [1.7]),
                        (InputType.Gyroscope, 'x'): Sequence([0], [100]), # DPS
                        (InputType.Gyroscope, 'y'): Sequence([0], [110]),
                        (InputType.Gyroscope, 'z'): Sequence([0], [120]),
                        (InputType.Magnetometer, 'x'): Sequence([0], [10000]), # milliGauss
                        (InputType.Magnetometer, 'y'): Sequence([0], [11000]),
                        (InputType.Magnetometer, 'z'): Sequence([0], [12000])
                    })
    return TestCase(end_condition, frames=[frame], test_points=[], aggregators={})

def blinky_test_case(with_oled=False):
    init_condition = Condition(ConditionType.After, 
                               cause=lambda req: req.arg == 'Loop')
    end_condition = Condition(ConditionType.After,
                              cause=5000, subconditions=[init_condition])
    frame = Frame(init_condition, end_condition, inputs={})

    points = []
    for i in range(1, 5):
        output_type, channel = OutputType.DigitalWrite, 13
        expected_value = 0
        if i%2==1:
            expected_value = 1

        points.append(TestPoint(
            frame_id=0,
            output_type=output_type,
            channel=channel,
            expected_value=expected_value,
            check_interval=(i*1000 + 100,i*1000 + 900),
            check_function=operator.eq,
            aggregator=all))

        if not with_oled:
            continue

        output_type, channel = OutputType.Screen, None
        expected_value = Screen(width=128, height=64) # Blank
        if i%2==1:
            rect = np.ones((10,20))
            expected_value.paint(rect, x=20, y=10)

        points.append(TestPoint(
            frame_id=0,
            output_type=output_type,
            channel=channel,
            expected_value=expected_value,
            check_interval=(i*1000 + 100,i*1000 + 900),
            check_function=operator.eq,
            aggregator=all))


    aggs = {(OutputType.DigitalWrite, 13): all, (OutputType.Screen, None): all}
    return TestCase(end_condition, frames=[frame], test_points=points, aggregators=aggs)

def button_test_case(with_oled=False):
    init_condition = Condition(ConditionType.After, 
                               cause=lambda req: req.arg == 'Loop')
    end_condition = Condition(ConditionType.After,
                              cause=5000, subconditions=[init_condition])
    frame = Frame(init_condition, end_condition,
                    inputs={
                        (InputType.DigitalRead, 6): Sequence(
                                                        [0,1000,2000,3000,4000,5000],
                                                        [1,0,1,0,1,0])
                    })

    points = []
    for i in range(1, 5):
        output_type, channel = OutputType.DigitalWrite, 13
        expected_value = 0
        if i%2==1:
            expected_value = 1

        points.append(TestPoint(
            frame_id=0,
            output_type=output_type,
            channel=channel,
            expected_value=expected_value,
            check_interval=(i*1000 + 100,i*1000 + 900),
            check_function=operator.eq,
            aggregator=all))

        if not with_oled:
            continue

        output_type, channel = OutputType.Screen, None
        expected_value = Screen(width=128, height=64) # Blank
        if i%2==1:
            rect = np.ones((10,20))
            expected_value.paint(rect, x=20, y=10)

        points.append(TestPoint(
            frame_id=0,
            output_type=output_type,
            channel=channel,
            expected_value=expected_value,
            check_interval=(i*1000 + 100,i*1000 + 900),
            check_function=operator.eq,
            aggregator=all))

    aggs = {(OutputType.DigitalWrite, 13): all, (OutputType.Screen, None): all}
    return TestCase(end_condition, frames=[frame], test_points=points, aggregators=aggs)


def main():
    #np.set_printoptions(threshold=np.nan)
    #case = constant_test_case()
    #case = blinky_test_case(with_oled=True)
    case = button_test_case(with_oled=True)
    result = run_test(case)
    print("Result:")
    print(result)