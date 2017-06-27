from . import utils
from .condition import Condition
from .sequence import Sequence
from .utils import BatchParams

class RequestLog:
    def __init__(self):
        self.requests = []

    def update(self, request):
        self.requests.append(request)

    def extract_sequences(self):
        sequences = {} # Maps (data_type, channel)-> Sequence
        def add_entry(data_type, channel, timestamp, value):
            key = (data_type, channel)
            if key not in sequences:
                sequences[key] = Sequence() # Initialize if necessary
            sequences[key].append(time=timestamp, value=value)

        for request in self.requests:
            if not request.is_valid:
                pass # Do nothing
            elif request.is_event:
                channel = None
                add_entry(request.data_type, channel, request.timestamp, request.arg)
            else: # inputs or outputs
                data_type = request.data_type
                channels = request.channels
                batch_params = request.batch_params
                for i in range(batch_params.num):
                    if request.values is not None:
                        values = request.values[i*len(channels):(i+1)*len(channels)]
                    else:
                        values = [None]*len(channels)

                    for (channel, value) in zip(channels, values):
                        if request.analog_params is not None: # Need to do ADC conversion
                            value = utils.digital_to_analog(value, request.analog_params)
                        timestamp = request.timestamp + i*batch_params.period
                        add_entry(data_type, channel, timestamp, value)

        return sequences

    def condition_satisfied_at(self, condition):
        # Make fresh copy (so stateful fields are reset)
        condition = Condition(condition.type, condition.cause, condition.subconditions)

        for request in self.requests:
            condition.update(request)
            if condition.is_satisfied():
                return condition.satisfied_at

        return None # Condition never satisfied

    def __eq__(self, other):
        return self.requests == other.requests #  conditions being equal is unnecessary

    def __str__(self):
        string = "RequestLog: requests={}"
        return string.format(self.requests)

    def __repr__(self):
        return str(self)




