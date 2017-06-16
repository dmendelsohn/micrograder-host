from request import *
from response import *
from collections import namedtuple

LogEntry = namedtuple('LogEntry', ['request', 'response', 'frame_id']) # Deprecate this perhaps?

class OutputLog:
    def __init__(self):
        self.outputs = {} # Maps (OutputType,channel)->list(TimedValue)
        self.frame_start_times = {} # Maps frame ID -> start_time

    # Successive calls must have increasing timestamps
    def record_output(self, output_type, channel, timestamp, value):
        key = (output_type, channel)
        if key not in self.outputs:
            self.outputs[key] = ValueSequence() # Initialize
        self.outputs[key].append(time=timestamp, value=value)

    def record_frame_start(self, frame_id, start_time):
        self.frame_start_times[frame_id] = start_time

class Test:
    def __init__(self, end_condition, frames, test_points, aggregators, preempt=True):
        self.end_condition = end_condition # Condition for overall test completion
        self.preempt = preempt # If True, later frame wins in when priority is tied
        self.frames = frames # List of frames
        self.test_points = test_points # List of expected output dicts for each frame
        self.aggregators = aggregators # Dict mapping (OutputType,channel)-> func(list(bool)->bool)

    # Return Response, frame_id
    def update(self, request): # request is a well-formed Request
        for frame in self.frames:
            frame.update(request)

        frame_id = self.get_current_frame_id()
        if request.is_input: # pass along request to specific frame
            if frame_id is None: # No frame is currently in progress
                response = ErrorResponse() # Cannot respond to request
            else:
                frame = self.frames[frame_id]
                values = [frame.get_value(timestamp=request.timestamp,
                                        input_type=request.data_type,
                                        channel=channel,
                                        analog_params=request.analog_params)
                            for channel in request.channels]

                analog = (request.analog_params is not None)
                if analog:
                    values = [utils.adc(value, request.analog_params) for value in values]

                response = ValuesResponse(values=values, analog=analog)

        else: # Regular ACK for non-inputs
            response = AckResponse()

        # Determine if end condition is satisfied
        self.end_condition.update(request)
        if self.end_condition.is_satisfied():
            response.test_complete = True
        else:
            response.test_complete = False

        return response

    # TODO: description
    def get_current_frame_id(self):
        actives = [(i, self.frames[i].priority, self.frames[i].start_time) 
                        for i in range(len(self.frames))if self.frames[i].is_active()]
        if len(actives) == 0:
            return None # No active frames
        highest_priority = max(actives, key=lambda x: x[1])
        priority_actives = list(filter(lambda x: x[1]==highest_priority, actives))
        priority_actives.sort(key=lambda x: x[2]) # Sort by start_time
        if self.preempt
            return priority_actives[-1][0] # Return id of frame with latest start_time
        else:
            return priority_actives[0][0] # Return id of frame with earlest start_time

    # Returns a dict mapping (OutputType,channel)->bool representing overall test for that key
    def assess(self, output_log):
        results = {} # Map from (OutputType,channel) to list(bool) representing relevant results
        for test_point in self.test_points:
            result = assess_test_point(test_point, output_log)
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


def assess_test_point(test_point, output_log):
    # Calculate start and end times
    if test_point.frame_id not in output_log.frame_start_times:
        return False # Frame never started, so this assessment could not be performed
    zero_point = output_log[test_point.frame_id]
    (start, end) = test_point.check_interval
    start += zero_point
    end += zero_point

    # Get relevant actual ouputs
    key = (test_point.output_type, test_point.channel)
    seq = output_log.outputs.get(key, ValueSequence())
    actual_outputs = seq.get_values(start, end)

    def check(actual_output):
        return test_point.check_function(test_point.expected_value, actual_output)

    return test_point.check_aggregator(map(check, actual_outputs))
    