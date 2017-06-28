from collections import namedtuple
from enum import Enum

TestCase = namedtuple("TestCase", ["handler", "evaluator"])

class InterpolationType(Enum):
    START = 0
    MID = 1
    END = 2
    LINEAR = 3

# This class stores information for constructing test cases dynamically
class Scaffold:
    def __init__(self, interpolations, template_points, aggregators):
        self.interpolations = interpolations # Map from (InputType,channel)->InterpolationType
        self.template_points = template_points # Map from (data_type,channel)->TestPoint
        self.aggregators = aggregators # Map from (data_type,channel)-> function list(bool)->bool
        #TODO: add specification for frame triggers
        #TODO: add specification for start/end buffers for frames

# Input: log is a RequestLog
# Input: scaffold is a Scaffold
# Returns: a TestCase build off that Scaffold using that log
def construct_test_case(log, scaffold):
    #TODO: implement
    pass