from src import case
from src import utils
from src.case import TestCase
from src.condition import Condition
from src.condition import ConditionType
from src.evaluator import Evaluator
from src.evaluator import TestPoint
from src.frame import Frame
from src.handler import RequestHandler
from src.request import EventType
from src.request import InputType
from src.request import OutputType
from src.sequence import Sequence
from src.screen import Screen

import numpy as np
import operator

def frameless_test_case(): # Good for making recordings
    end_condition = Condition(ConditionType.After, cause=10**10)
    handler = RequestHandler(end_condition=end_condition, frames=[])
    evaluator = Evaluator(conditions=[], test_points=[], aggregators={})
    return TestCase(handler=handler, evaluator=evaluator)
 
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
    handler = RequestHandler(end_condition=end_condition, frames=[frame])
    evaluator = Evaluator(conditions=[], test_points=[], aggregators={})
    return TestCase(handler=handler, evaluator=evaluator)

def blinky_test_case(with_oled=False):
    init_condition = Condition(ConditionType.After, 
                               cause=lambda req: req.arg == 'Start')
    end_condition = Condition(ConditionType.After,
                              cause=5000, subconditions=[init_condition])
    frame = Frame(init_condition, end_condition, inputs={})
    handler = RequestHandler(end_condition=end_condition, frames=[frame])

    points = []
    for i in range(1, 5):
        output_type, channel = OutputType.DigitalWrite, 13
        expected_value = 0
        if i%2==1:
            expected_value = 1

        points.append(TestPoint(
            condition_id=0,
            data_type=output_type,
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
            condition_id=0,
            data_type=output_type,
            channel=channel,
            expected_value=expected_value,
            check_interval=(i*1000 + 100,i*1000 + 900),
            check_function=operator.eq,
            aggregator=all))

    aggs = {(OutputType.DigitalWrite, 13): all, (OutputType.Screen, None): all}
    evaluator = Evaluator(conditions=[init_condition], test_points=points, aggregators=aggs)
    return TestCase(handler=handler, evaluator=evaluator)

def button_test_case(with_oled=False):
    init_condition = Condition(ConditionType.After,
                               cause=lambda req: req.arg == 'Start')
    end_condition = Condition(ConditionType.After,
                               cause=5000, subconditions=[init_condition])
    frame = Frame(init_condition, end_condition,
                    inputs={
                        (InputType.DigitalRead, 6): Sequence(
                                                        [0,1000,2000,3000,4000,5000],
                                                        [1,0,1,0,1,0])
                    })
    handler = RequestHandler(end_condition=end_condition, frames=[frame])

    points = []
    for i in range(1, 5):
        output_type, channel = OutputType.DigitalWrite, 13
        expected_value = 0
        if i%2==1:
            expected_value = 1

        points.append(TestPoint(
            condition_id=0,
            data_type=output_type,
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
            condition_id=0,
            data_type=output_type,
            channel=channel,
            expected_value=expected_value,
            check_interval=(i*1000 + 100,i*1000 + 900),
            check_function=operator.eq,
            aggregator=all))

    aggs = {(OutputType.DigitalWrite, 13): all, (OutputType.Screen, None): all}
    evaluator = Evaluator(conditions=[init_condition], test_points=points, aggregators=aggs)
    return TestCase(handler=handler, evaluator=evaluator)

# Saves a bunch of hardcoded test_cases to files
def construct_hardcode(verbose=False):
    if verbose:
        print("Constructing test cases and saving to files")

    case = frameless_test_case()
    filepath = "resources/frameless.tc"
    utils.save(case, filepath)

    case = constant_test_case()
    filepath = "resources/constant.tc"
    utils.save(case, filepath)

    case = blinky_test_case(with_oled=False)
    filepath = "resources/blinky.tc"
    utils.save(case, filepath)

    case = blinky_test_case(with_oled=True)
    filepath = "resources/blinky_oled.tc"
    utils.save(case, filepath)

    case = button_test_case(with_oled=False)
    filepath = "resources/button.tc"
    utils.save(case, filepath)

    case = button_test_case(with_oled=True)
    filepath = "resources/button_oled.tc"
    utils.save(case, filepath)

# Input: log is a RequestLog
# Input: scaffold is a Scaffold
# Returns: a TestCase build off that Scaffold using that log
def construct_dynamic(log, scaffold):
    return scaffold.generate_test_case(log)

def default_scaffold():
    # TODO: return a Scaffold
    pass

def main(logpath=None, verbose=False):
    if logpath:
        log = utils.load(logpath)
        scaffold = default_scaffold() # Later, make this from a file as well
        test_case = construct_dynamic(log, scaffold)
        utils.save(test_case, "resources/temp.tc") # TODO: make this dynamically chosen
    else:
        construct_hardcode(verbose)
