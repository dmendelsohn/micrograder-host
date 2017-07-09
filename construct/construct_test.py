from src import case
from src import utils
from src.case import TestCase
from src.condition import Condition
from src.condition import ConditionType
from src.evaluator import Evaluator
from src.evaluator import TestPoint
from src.frame import Frame
from src.handler import RequestHandler
from src.scaffold import FrameTemplate
from src.scaffold import Scaffold
from src.scaffold import TestPointTemplate
from src.sequence import InterpolationType
from src.sequence import Sequence
from src.screen import Screen
from src.utils import EventType
from src.utils import InputType
from src.utils import OutputType

import numpy as np
import operator

# Good for testing
quirky_defaults={
    InputType.DigitalRead: Sequence([0],[1]),
    InputType.AnalogRead: Sequence([0],[1650]), # 1.65V
    (InputType.Accelerometer, 'x'): Sequence([0], [1.5]), # 1.5Gs
    (InputType.Accelerometer, 'y'): Sequence([0], [1.6]),
    (InputType.Accelerometer, 'z'): Sequence([0], [1.7]),
    (InputType.Gyroscope, 'x'): Sequence([0], [100]), # DPS
    (InputType.Gyroscope, 'y'): Sequence([0], [110]),
    (InputType.Gyroscope, 'z'): Sequence([0], [120]),
    (InputType.Magnetometer, 'x'): Sequence([0], [10000]), # milliGauss
    (InputType.Magnetometer, 'y'): Sequence([0], [11000]),
    (InputType.Magnetometer, 'z'): Sequence([0], [12000])
}

def is_start_msg(request):
    return request.data_type == EventType.Print and request.arg == "Start"

# TODO: update this once I've updated the embedded wifi lib
def is_wifi_request(request):
    return request.data_type == EventType.Print and request.arg == "Wifi Request"

# TODO: update this once I've updated the embedded wifi lib
def is_wifi_response(request):
    return request.data_type == EventType.Print and request.arg == "Wifi Response"

 # Good for making recordings, or for basic tests
def blank_case(duration=10**12, default_values=None):
    end_condition = Condition(ConditionType.After, cause=duration)
    handler = RequestHandler(end_condition=end_condition, default_values=default_values)
    evaluator = Evaluator(conditions=[], test_points=[])
    return TestCase(handler=handler, evaluator=evaluator)

def blinky_test_case(with_oled=False):
    init_condition = Condition(ConditionType.After, 
                               cause=is_start_msg)
    end_condition = Condition(ConditionType.After,
                              cause=5*(10**3), subconditions=[init_condition])
    handler = RequestHandler(end_condition=end_condition)

    points = []
    for i in range(1, 5):
        output_type, channel = OutputType.DigitalWrite, 13
        expected_value = 0
        if i%2==1:
            expected_value = 1

        start = (i+0.1)*(10**3)
        end = (i+0.9)*(10**3)

        points.append(TestPoint(
            condition_id=0,
            data_type=output_type,
            channel=channel,
            expected_value=expected_value,
            check_interval=(start,end)))

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
            check_interval=(start,end)))

    evaluator = Evaluator(conditions=[init_condition], test_points=points)
    return TestCase(handler=handler, evaluator=evaluator)

def button_test_case(with_oled=False):
    init_condition = Condition(ConditionType.After,
                               cause=is_start_msg)
    end_condition = Condition(ConditionType.After,
                               cause=5*(10**3), subconditions=[init_condition])

    seq = Sequence(times=[i*10**3 for i in range(6)], values=[1,0,1,0,1,0])
    frame = Frame(init_condition, end_condition,
                    inputs={(InputType.DigitalRead, 6): seq})
    handler = RequestHandler(end_condition=end_condition, frames=[frame])

    points = []
    for i in range(1, 5):
        output_type, channel = OutputType.DigitalWrite, 13
        expected_value = 0
        if i%2==1:
            expected_value = 1

        start = (i+0.1)*(10**3)
        end = (i+0.9)*(10**3)

        points.append(TestPoint(
            condition_id=0,
            data_type=output_type,
            channel=channel,
            expected_value=expected_value,
            check_interval=(start,end)))

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
            check_interval=(start,end)))

    evaluator = Evaluator(conditions=[init_condition], test_points=points)
    return TestCase(handler=handler, evaluator=evaluator)

# Saves a bunch of hardcoded test_cases to files
def construct_hardcode(verbose=False):
    if verbose:
        print("Constructing test cases and saving to files")

    case = blank_case(default_values=quirky_defaults)
    filepath = "resources/cases/blank.tc"
    utils.save(case, filepath)

    case = blinky_test_case(with_oled=True)
    filepath = "resources/cases/blinky_oled.tc"
    utils.save(case, filepath)

    case = button_test_case(with_oled=True)
    filepath = "resources/cases/button_oled.tc"
    utils.save(case, filepath)

# Input: log is a RequestLog
# Input: scaffold is a Scaffold
# Returns: a TestCase build off that Scaffold using that log
def construct_dynamic(log, scaffold):
    return scaffold.generate_test_case(log)

# num_frames must be int >= 1
def default_scaffold(num_frames=1):
    def is_start_request(request):
        return request.data_type == EventType.Print and request.arg == "Start"
    start_condition = Condition(ConditionType.After, cause=is_start_request)
    end_condition = Condition(ConditionType.After, cause=5*10**3, subconditions=[start_condition])
    frame_templates = [FrameTemplate(start_condition=start_condition,
                                     end_condition=None)] # end_cond is None => end of log
    for i in range(num_frames-1):
        prev_start = frame_templates[-1].start_condition
        prev_end = Condition(ConditionType.After, cause=is_wifi_request,
                             subconditions=[prev_start])
        frame_templates[-1].end_condition = prev_end

        start_condition = Condition(ConditionType.After, cause=is_wifi_response,
                                    subconditions=[prev_end])
        new_template = FrameTemplate(start_condition=start_condition, end_condition=None)
        frame_templates.append(new_template)

    defaults = utils.DEFAULT_VALUES.copy()
    defaults[InputType.DigitalRead] = 1 # Button presses are active low
    return Scaffold(frame_templates=frame_templates,
                    defaults=defaults)

def main(logpath=None, testcasepath=None, verbose=False, num_frames=1):
    if logpath:
        log = utils.load(logpath)
        scaffold = default_scaffold(num_frames) # Later, make scaffolds loadable from files as well
        test_case = construct_dynamic(log, scaffold)
        try:
            utils.save(test_case, testcasepath)
        except:
            path = "resources/cases/temp.tc"
            print("Failed to save to given testcasepath, using {} instead".format(path))
            utils.save(test_case, path)
    else:
        construct_hardcode(verbose)
