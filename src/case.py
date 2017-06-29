from collections import namedtuple
from enum import Enum

TestCase = namedtuple("TestCase", ["handler", "evaluator"])
ScaffoldParmas = namedtuple("ScaffoldParams", []) # TODO

class InterpolationType(Enum):
    START = 0 # Position samples are start of range
    MID = 1 # Position samples in middle of range
    END = 2 # Position samples at end of range
    LINEAR = 3 # Interpolate linearly between samples

# Check_interval is relative to observed time of point, not any condition
# Either elemnt of check_interval tuple can be string, it will be eval-ed
# In string expression for check_interval elt, use "T" as length of this output
TestPointTemplate = namedtuple('TestPointTemplate', ['data_type',
                                                     'channel',
                                                     'check_interval', # Relative to observed time
                                                     'check_function',
                                                     'aggregator',
                                                     ])

FrameTemplate = namedtuple('FrameTemplate', ['start_condition',
                                             'end_condition',
                                             'priority',
                                             'input_initialization', # if True, insert default input at t=0
                                             ])

# This class stores information for constructing test cases dynamically
class Scaffold:
    def __init__(self,
                 frame_templates,
                 interpolations, defaults,
                 point_templates, aggregators):
        self.frame_templates = frame_templates # List of FrameTemplates
        self.interpolations = interpolations # Map from (InputType,channel)->InterpolationType
        self.defaults = defaults # Map from (InputType,channel)->value
        self.point_templates = point_templates # Map from (data_type,channel)->TestPointTemplate
        self.aggregators = aggregators # Map from (data_type,channel)-> function list(bool)->bool

    # Input: a RequestLog
    # Retunrs a TestCase
    # TestCase includes "background" frame (always active, priority=-1, default input values)
    def generate_test_case(self, log):
        # Generate background frame
        # For each frame_template:
        #   determine start and end times (default end time is last request in the log)
        #   if start_time < end_time, set up the frame
        #       For each input, consider subsequence in range. Shift. Add lead_in point. Interpolate.
        #       For each output in range, construct test_point
        # Construct TestCase = (handler, evaluator) and return
        pass
