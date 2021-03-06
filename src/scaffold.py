from . import prefs
from . import utils
from .case import TestCase
from .condition import Condition
from .condition import ConditionType
from .evaluator import EvalPoint
from .evaluator import Evaluator
from .frame import Frame
from .handler import RequestHandler
from .prefs import Preferences
from .sequence import InterpolationType
from .utils import InputType
from .utils import OutputType

import operator

DEFAULT_CHECK_INTERVAL = ("0.2*T", "0.8*T")

# Check_interval is relative to observed time of point, not any condition
# Either elemnt of check_interval tuple can be string, it will be eval-ed
# In string expression for check_interval elt, use "T" as length of this output
class EvalPointTemplate:
    def __init__(self, check_interval=DEFAULT_CHECK_INTERVAL,
                 check_function=operator.eq, portion=1.0):
        self.check_interval = check_interval
        self.check_function = check_function
        self.portion = portion

class FrameTemplate:
    def __init__(self, start_condition, end_condition, *,
                 priority=0, init_to_default=True):
        self.start_condition = start_condition
        self.end_condition = end_condition # If None: gets resolved later
        self.priority = priority
        self.init_to_default = init_to_default

# This class stores information for constructing test cases dynamically
class Scaffold:
    def __init__(self, frame_templates,
                 interpolations=None, default_values=None,
                 point_templates=None, aggregators=None):

        if interpolations is None:
            interpolations = Preferences({tuple(): InterpolationType.Mid})
        if default_values is None:
            default_values = prefs.default_default_values()
        if point_templates is None:
            point_templates = Preferences({tuple(): EvalPointTemplate()})
        if aggregators is None:
            aggregators = prefs.default_aggregators()

        self.frame_templates = frame_templates # List of FrameTemplates
        self.interpolations = interpolations # Preferences<InterpolationType>
        self.default_values = default_values # Preferences<value>
        self.point_templates = point_templates # Preferences<EvalPointTemplate>
        self.aggregators = aggregators # Preferences<f(list of bool)->bool>

    # Input: a RequestLog
    # Returns a TestCase
    # TestCase includes "background" frame (always active, priority=-1, default input values)
    def generate_test_case(self, log):
        # First, filter out None-valued input requests (true requests)
        def f(request):
            return not (request.is_input and request.values is None)
        log = log.filter(f)

        overall_sequences = log.extract_sequences()

        frames = []
        points_by_frame = []
        for frame_template in self.frame_templates:
            bounds = self.generate_frame_bounds(log, frame_template)
            if bounds:
                (start_time, end_time) = bounds
                if frame_template.end_condition is None: # Need to generate it
                    frame_template.end_condition = Condition(ConditionType.After,
                                    cause=(end_time-start_time),
                                    subconditions=[frame_template.start_condition])

                # Generate relative input sequences that occurred in this frame
                inputs = self.generate_inputs(overall_sequences, start_time, end_time,
                                              frame_template.init_to_default)
                frames.append(Frame(start_condition=frame_template.start_condition,
                                    end_condition=frame_template.end_condition,
                                    inputs=inputs,
                                    priority=frame_template.priority))

                # Generate points for all outputs that occurred during this frame
                new_points = self.generate_eval_points(overall_sequences, start_time, end_time)
                for key in new_points:
                    for point in new_points[key]:
                        point.condition_id = len(frames)-1
                points_by_frame.append(new_points)

        points = {} # Combination of point dicts from all frames
        for subpoint in points_by_frame:
            for key in subpoint:
                if key not in points:
                    points[key] = []
                points[key].extend(subpoint[key])

        handler_end_condition = Condition(ConditionType.And,
                                          subconditions=[frame.end_condition for frame in frames])
        handler = RequestHandler(end_condition=handler_end_condition, frames=frames, preempt=True)
        evaluator = Evaluator(conditions=[frame.start_condition for frame in frames],
                              points=points,
                              aggregators=self.aggregators)
        return TestCase(handler=handler, evaluator=evaluator)

    # If both start and end conditions of the frame_template are met in the 
    # log, and the start condition is met first, return (start_time, end_time)
    # Otherwise, return None
    def generate_frame_bounds(self, log, frame_template):
        start_time = log.condition_satisfied_at(frame_template.start_condition)
        if frame_template.end_condition is None:
            end_time = log.get_end_time()
        else:
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
                        start_value = self.default_values.get_preference((data_type, channel))
                    subsequence.insert(time=0, value=start_value)

                interpolation_type = self.interpolations.get_preference((data_type, channel))
                subsequence = subsequence.interpolate(interpolation_type, res=utils.MILLISECOND)
                inputs[(data_type,channel)] = subsequence
        return inputs

    # Generates EvalPoints based on non-redundant outputs in the specified
    # range in the overall sequence
    # For each non-redundant output, we use the relevant template point,
    # and fill in check_interval, condition_id (given to this function) and expeccted_value
    # Input: overall_sequences: map from (data_type,channel)->Sequence, in absolute time
    # Input: start_time, end_time: an interval with usual inclusiveness rules
    # Returns: dict mapping (data_type, channel)->(list of EvalPoints)
    def generate_eval_points(self, overall_sequences, start_time, end_time):
        points = {}
        for (data_type, channel) in overall_sequences:
            if type(data_type) is OutputType:
                key = (data_type, channel)
                point_template = self.point_templates.get_preference(key)
                sequence = overall_sequences[key]
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

                    point = EvalPoint(condition_id=-1, # Filled in later
                                      expected_value=sequence[i].value,
                                      check_interval=(start,end),
                                      check_function=point_template.check_function,
                                      portion=point_template.portion)
                    if key not in points:
                        points[key] = []
                    points[key].append(point)
        return points
