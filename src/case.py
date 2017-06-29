from collections import namedtuple
from enum import Enum

from .evaluator import Evaluator
from .frame import Frame
from .handler import RequestHandler
from .request import InputType
from .request import OutputType

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
                                             'initialize_to_default', # if True, insert default input at t=0
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
        # First, filter out None-valued input requests (true requests)
        def f(request):
            return not (request.is_input and request.values is None)
        log = log.filter(f)

        overall_end_time = log.get_end_time()
        overall_sequences = log.extract_sequences()

        frames = []
        test_points = []
        for frame_template in self.frame_templates:
            bounds = self.generate_frame_bounds(log, frame_template)
            if bounds:
                (start_time, end_time) = bounds

                # Generate relative input sequences that occurred in this frame
                inputs = self.generate_inputs(overall_sequences, start_time, end_time,
                                              frame_template.initialize_to_default)
                frames.append(Frame(start_condition=frame_template.start_condition,
                                    end_condition=frame_template.end_condition,
                                    inputs=inputs,
                                    priority=frame_template.priority))

                # Generate test_points for all outputs that occurred during this frame
                condition_id = len(frames)-1
                test_points.extend(self.generate_test_points(overall_sequences, start_time, 
                                                             end_time, condition_id))

                # TODO: construct relevant test_points and add to test_points list
                #    Don't forget to remove redundancies

        handler_end_condition = Condition(ConditionType.And,
                                          subconditions=[frame.end_condition for frame in frames])
        handler = RequestHandler(end_condition=handler_end_condition, frames=frames, preempt=True)
        evaluator = Evaluator(conditions=[frame.start_condition for frame in frames],
                              test_points=test_points,
                              aggregators=self.aggregators)
        return TestCase(handler=handler, evaluator=evaluator)

    #TOOD: description
    def generate_frame_bounds(self, log, frame_template):
        start_time = log.condition_satisfied_at(frame_template.start_condition)
        end_time = log.condition_satisfied_at(frame_template.end_condition)

        if start_time is not None and end_time is not None and start_time < end_time:
            return (start_time, end_time)
        else:
            return None

    # TODO: description
    def generate_inputs(self, overall_sequences, start_time, end_time):
        inputs = {}
        for (data_type, channel) in overall_sequences:
            if type(data_type) is InputType:
                sequence = overall_sequences[(data_type,channel)]
                sequence = sequence.get_subsequence(start_time, end_time)
                sequence = sequence.shift(-start_time)
                #TODO: insert a lead in point
                #TODO: interpolate
                inputs[(data_type,channel)] = sequence
        return inputs

    # TODO: description
    def generate_test_points(self, overall_sequences, start_time, end_time, condition_id):
        test_points = []
        for (data_type, channel) in overall_sequences:
            if type(data_type) is OutputType:
                sequence = overall_sequences[(data_type,channel)]
                sequence = sequence.get_subsequence(start_time, end_time)
                sequence = sequence.shift(-start_time)
                sequence = sequence.remove_duplicates()
                #TODO: for (time, value) in sequence:
                #   create a new test point
        return test_points
