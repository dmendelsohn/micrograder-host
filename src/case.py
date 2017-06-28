from collections import namedtuple
from enum import Enum

TestCase = namedtuple("TestCase", ["handler", "evaluator"])
ScaffoldParmas = namedtuple("ScaffoldParams", []) # TODO

class InterpolationType(Enum):
    START = 0
    MID = 1
    END = 2
    LINEAR = 3

# This class stores information for constructing test cases dynamically
class Scaffold:
    def __init__(self, interpolations, template_points, aggregators, frame_triggers, params):
        self.interpolations = interpolations # Map from (InputType,channel)->InterpolationType
        self.template_points = template_points # Map from (data_type,channel)->TestPoint
        self.aggregators = aggregators # Map from (data_type,channel)-> function list(bool)->bool
        self.frame_triggers # A list of Conditions that, if met, are start_condition for a frame
        self.params = params # ScaffoldParams

    # Input: a RequestLog
    # Retunrs a TestCase
    def generate_test_case(self, log):
        #TODO: implement
        pass