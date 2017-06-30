from collections import namedtuple
from enum import Enum

from . import utils
from .condition import Condition
from .condition import ConditionType
from .evaluator import Evaluator
from .evaluator import TestPoint
from .frame import Frame
from .handler import RequestHandler
from .request import InputType
from .request import OutputType

TestCase = namedtuple("TestCase", ["handler", "evaluator"])


# Check_interval is relative to observed time of point, not any condition
# Either elemnt of check_interval tuple can be string, it will be eval-ed
# In string expression for check_interval elt, use "T" as length of this output
TestPointTemplate = namedtuple('TestPointTemplate', ['check_interval', # Relative to observed time
                                                     'check_function',
                                                     'aggregator',
                                                     ])

FrameTemplate = namedtuple('FrameTemplate', ['start_condition',
                                             'end_condition',
                                             'priority',
                                             'init_to_default', # if True, insert default input at t=0
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

        overall_sequences = log.extract_sequences()

        frames = []
        test_points = []
        for frame_template in self.frame_templates:
            bounds = self.generate_frame_bounds(log, frame_template)
            if bounds:
                (start_time, end_time) = bounds

                # Generate relative input sequences that occurred in this frame
                inputs = self.generate_inputs(overall_sequences, start_time, end_time,
                                              frame_template.init_to_default)
                frames.append(Frame(start_condition=frame_template.start_condition,
                                    end_condition=frame_template.end_condition,
                                    inputs=inputs,
                                    priority=frame_template.priority))

                # Generate test_points for all outputs that occurred during this frame
                condition_id = len(frames)-1
                test_points.extend(self.generate_test_points(overall_sequences, start_time, 
                                                             end_time, condition_id))


        handler_end_condition = Condition(ConditionType.And,
                                          subconditions=[frame.end_condition for frame in frames])
        handler = RequestHandler(end_condition=handler_end_condition, frames=frames, preempt=True)
        evaluator = Evaluator(conditions=[frame.start_condition for frame in frames],
                              test_points=test_points,
                              aggregators=self.aggregators)
        return TestCase(handler=handler, evaluator=evaluator)

    # If both start and end conditions of the frame_template are met in the 
    # log, and the start condition is met first, return (start_time, end_time)
    # Otherwise, return None
    def generate_frame_bounds(self, log, frame_template):
        start_time = log.condition_satisfied_at(frame_template.start_condition)
        end_time = log.condition_satisfied_at(frame_template.end_condition)

        if start_time is not None and end_time is not None and start_time < end_time:
            return (start_time, end_time)
        else:
            return None

    # Generates input sequences based on all InputRequests in a given time frame
    # Sequences have t=0 at start_time
    # overall_sequences: (data_type,channel)->Sequence dict from the log
    # start_time, end_time: start is inclusive, end is not.  As usual.
    # init_to_default: if necessary, prefer to fill in t=0 to first value with the default
    #       (rather than the t<0 value)
    # Returns: (InputType,channel)->Sequence to be used as the inputs attribute for a Frame
    def generate_inputs(self, overall_sequences, start_time, end_time, init_to_default):
        inputs = {}
        for (data_type, channel) in overall_sequences:
            if type(data_type) is InputType:
                sequence = overall_sequences[(data_type,channel)]
                subsequence = sequence.get_subsequence(start_time, end_time)
                subsequence.shift(-start_time)
                if len(subsequence) < 1 or subsequence[0].time > 0: # Need to insert initial point
                    start_value = sequence.get_sample(start_time)
                    if init_to_default or start_value is None: # Use default
                        start_value = self.defaults[(data_type,channel)]
                        if start_value is None:
                            #Later: handle unspecified default
                            pass
                    subsequence.insert(time=0, value=start_value)

                interpolation_type = self.interpolations[(data_type,channel)]
                subsequence = subsequence.interpolate(interpolation_type, res=utils.MILLISECOND)
                inputs[(data_type,channel)] = subsequence
        return inputs

    # Generates test_points based on non-redundant outputs in the specified
    # range in the overall sequence
    # For each non-redundant output, we use the relevant template point,
    # and fill in check_interval, condition_id (given to this function) and expeccted_value
    # Input: overall_sequences: map from (data_type,channel)->Sequence, in absolute time
    # Input: start_time, end_time: an interval with usual inclusiveness rules
    # Input: condution_id: index of a condition that was presumable met at start_time
    # Returns: a list of test_points
    def generate_test_points(self, overall_sequences, start_time, end_time, condition_id):
        test_points = []
        for (data_type, channel) in overall_sequences:
            if type(data_type) is OutputType:
                point_template = self.point_templates[(data_type,channel)]
                sequence = overall_sequences[(data_type,channel)]
                sequence = sequence.get_subsequence(start_time, end_time)
                sequence.shift(-start_time)
                sequence.remove_duplicates()
                for i in range(len(sequence)):

                    # Make T so we can "eval" it in start and end strings
                    if i+1 < len(sequence):
                        T = sequence[i+1].time - sequence[i].time
                    else:
                        T = (end_time - start_time) - sequence[i].time
                    start, end = point_template.check_interval
                    start = int(eval(str(start))) + sequence[i].time
                    end = int(eval(str(end))) + sequence[i].time

                    point = TestPoint(condition_id=condition_id,
                                      data_type=data_type,
                                      channel=channel,
                                      expected_value=sequence[i].value,
                                      check_interval=(start,end),
                                      check_function=point_template.check_function,
                                      aggregator=point_template.aggregator)
                    test_points.append(point)
        return test_points
