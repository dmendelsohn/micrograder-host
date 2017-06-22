from collections import namedtuple

from . import utils
from .response import AckResponse
from .response import ErrorResponse
from .sequence import Sequence

class OutputLog:
    def __init__(self):
        self.outputs = {} # Maps (OutputType,channel)-> Sequence
        self.frame_start_times = {} # Maps frame ID -> start_time

    # Successive calls must have increasing timestamps
    def record_output(self, output_type, channel, timestamp, value):
        key = (output_type, channel)
        if key not in self.outputs:
            self.outputs[key] = Sequence() # Initialize
        self.outputs[key].append(time=timestamp, value=value)

    def record_frame_start(self, frame_id, start_time):
        self.frame_start_times[frame_id] = start_time

    def __eq__(self, other):
        return (self.outputs == other.outputs and 
                self.frame_start_times == other.frame_start_times)

    def __str__(self):
        string = "OutputLog: outputs={}, frame_start_times={}"
        return string.format(self.outputs, self.frame_start_times)


TestPoint = namedtuple('TestPoint', ['frame_id',
                                     'output_type',
                                     'channel',
                                     'expected_value',
                                     'check_interval',
                                     'check_function',
                                     'aggregator'])

class TestCase:
    def __init__(self, end_condition, frames, test_points, aggregators, preempt=True):
        self.end_condition = end_condition # Condition for overall test completion
        self.preempt = preempt # If True, later frame wins in when priority is tied
        self.frames = frames # List of frames
        self.test_points = test_points # List of test points
        self.aggregators = aggregators # Dict mapping (OutputType,channel)-> func(list(bool)->bool)
        self.output_log = OutputLog()

    # Return Response, frame_id
    def update(self, request): # request is a well-formed Request
        for frame in self.frames:
            frame.update(request)

        frame_id = self.get_current_frame_id()
        if request.is_input: # pass along request to specific frame
            if frame_id is None: # No frame is currently in progress
                response = ErrorResponse() # Cannot respond to request
            elif request.values is not None: # This was a recording, not a real request
                response = ErrorResponse() # We shouldn't get this type of request in a live test
            else:
                frame = self.frames[frame_id]
                response = frame.get_response(request)

        else: # Regular ACK for non-inputs
            if request.is_output: # Log it
                output_type = request.data_type
                for (channel, value) in zip(request.channels, request.values):
                    if request.analog_params is not None:  # Need to convert digital to analog
                        value = utils.digital_to_analog(value, request.analog_params)
                    self.output_log.record_output(output_type, channel, request.timestamp, value)

            response = AckResponse()

        # Determine if end condition is satisfied
        self.end_condition.update(request)
        if self.end_condition.is_satisfied():
            response.test_complete = True
        else:
            response.test_complete = False

        return response

    # Returns the id of the frame that is currently prioritized to serve an input request
    def get_current_frame_id(self):
        actives = [(i, self.frames[i].priority, self.frames[i].start_time) 
                        for i in range(len(self.frames)) if self.frames[i].is_active()]
        if len(actives) == 0:
            return None # No active frames
        highest_priority = max(a[1] for a in actives)
        priority_actives = list(filter(lambda a: a[1]==highest_priority, actives))
        priority_actives.sort(key=lambda a: a[2]) # Sort by start_time
        if self.preempt:
            return priority_actives[-1][0] # Return id of frame with latest start_time
        else:
            return priority_actives[0][0] # Return id of frame with earlest start_time

    # Returns a dict mapping (OutputType,channel)->bool representing overall test for that key
    def assess(self):
        for i in range(len(self.frames)):
            t = self.frames[i].start_time
            if t is not None:
                self.output_log.record_frame_start(frame_id=i, start_time=t)

        #print(self.output_log)
        results = {} # Map from (OutputType,channel) to list(bool) representing relevant results
        for test_point in self.test_points:
            #print(test_point)
            result = assess_test_point(test_point, self.output_log)
            #print(result)
            key = (test_point.output_type, test_point.channel)
            if key not in results:
                results[key] = [] # Initialize
            results[key].append(result)

        # Now, for each (OutputType,channel), aggregate results to a single boolean
        for key in results:
            if key in self.aggregators:
                agg = self.aggregators[key]
                results[key] = agg(results[key])
            else: # No aggregator for this outputType,channel
                results[key] = False
        return results

# Assesses if a single test point passes
def assess_test_point(test_point, output_log):
    # Calculate start and end times
    if test_point.frame_id not in output_log.frame_start_times:
        return False # Frame never started, so this assessment could not be performed

    zero_point = output_log.frame_start_times[test_point.frame_id]
    (start, end) = test_point.check_interval
    start += zero_point
    end += zero_point

    # Get relevant actual ouputs
    key = (test_point.output_type, test_point.channel)
    seq = output_log.outputs.get(key, Sequence())
    actual_outputs = seq.get_values(start, end)

    def check(actual_output):
        return test_point.check_function(test_point.expected_value, actual_output)

    return test_point.aggregator(map(check, actual_outputs))
