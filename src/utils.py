from collections import namedtuple
import dill as pickle
from enum import Enum
import numpy as np
import operator
import struct

MILLISECOND = 1 # time unit(s) per millisecond

class InputType(Enum):
    Accelerometer = 1
    Gyroscope = 2
    Magnetometer = 3
    DigitalRead = 4
    AnalogRead = 5

class OutputType(Enum):
    DigitalWrite = 1
    AnalogWrite = 2
    Screen = 3

class EventType(Enum):
    Init = 1
    ScreenInit = 2
    Print = 3
    Wifi = 4
    Gps = 5

# If no channel is specified, that's a default across all channels
# If both input_type and (input_type,channel) are keys, more specific default "wins"
DEFAULT_VALUES = {
    InputType.DigitalRead: 0,
    InputType.AnalogRead: 0,
    InputType.Accelerometer: 0,
    (InputType.Accelerometer, 'z'): 1, # Gravity baked in by default on 'z' channel
    InputType.Gyroscope: 0,
    InputType.Magnetometer: 0,
}

DEFAULT_CHECK_FUNCTIONS = {
    None: operator.__eq__
}

DEFAULT_AGGREGATORS = {
    None: all
}

def get_default_value(data_type, channel=None, defaults=DEFAULT_VALUES):
    return get_default(data_type, channel, defaults)

def get_default_check_function(data_type, channel=None, defaults=DEFAULT_CHECK_FUNCTIONS):
    return get_default(data_type, channel, defaults)

def get_default_aggregator(data_type, channel=None, defaults=DEFAULT_AGGREGATORS):
    return get_default(data_type, channel, defaults)


# Generic helper function for getting a values for Inputs, Outputs, Requests
# First check if (data_type, channel) is key in defaults, and return value
# If not, check if (data_type) is key in defaults, and return value
# If not, check if there None is key in defaults, and return value
# Else return None
def get_default(data_type, channel, defaults):
    if (data_type,channel) in defaults:
        return defaults[(data_type, channel)]
    elif data_type in defaults:
        return defaults[data_type] # Across all channels
    elif None in defaults:
        return defaults[None]
    else:
        return None


# value: a numeric
# params: of type AnalogParams
# Returns "bin" for value according to the params (with bounding)
def analog_to_digital(value, params):
    frac = (value - params.min_value) / (params.max_value - params.min_value)
    raw_bin = round(frac * (params.max_bin - params.min_bin) + params.min_bin)
    bounded_bin = min(params.max_bin, max(params.min_bin, raw_bin))
    return bounded_bin

# value: an int representing "bin"
# params: of type AnanlogParams
# Returns analog value according to params (with bounding)
def digital_to_analog(value, params):
    frac = (value - params.min_bin) / (params.max_bin - params.min_bin)
    raw_value = frac * (params.max_value - params.min_value) + params.min_value
    bounded_value = min(params.max_value, max(params.min_value, raw_value))
    return bounded_value

# Code for byte encoding/decoding for integers
FORMAT_CHARS = {
    (1,False): 'B', (1,True): 'b',
    (2,False): 'H', (2,True): 'h',
    (4,False): 'I', (4,True): 'i',
    (8,False): 'Q', (8,True): 'q'
}

# Decodes an integer from bytes, little-endian and returns it as an int
# raw_bytes must be of length 1, 2, 4, 8
def decode_int(raw_bytes, signed=False):
    width = len(raw_bytes)
    if (width,signed) in FORMAT_CHARS:
        format_char = FORMAT_CHARS[(width,signed)]
        try:
            return struct.unpack('<' + format_char, raw_bytes)[0]
        except struct.error as e:
            raise e
    else:
        raise ValueError('Could not decode {} with signed={}'.format(raw_bytes, signed))

# Encodes an integer (num) as bytes, little-endian.  Note that width is byte-width, not bit-width
# width must be 1, 2, 4, or 8
def encode_int(num, width=4, signed=False):
    if (width,signed) in FORMAT_CHARS:
        format_char = FORMAT_CHARS[(width,signed)]
        try:
            return struct.pack('<' + format_char, num)
        except struct.error as e:
            raise e
    else:
        raise ValueError('Invalid encode width={} bytes with signed={}'.format(width, signed))


AnalogParams = namedtuple('AnalogParams', ['min_bin', 'max_bin', 'min_value', 'max_value'])

# Input: bytes of length 16 and interpret as 4 int32s
# Return: AnalogParams
def decode_analog_params(raw):
    min_bin = decode_int(raw[0:4], signed=True)
    max_bin = decode_int(raw[4:8], signed=True)
    min_value = decode_int(raw[8:12], signed=True)
    max_value = decode_int(raw[12:16], signed=True)
    return AnalogParams(min_bin, max_bin, min_value, max_value)

BatchParams = namedtuple('BatchParams', ['num', 'period']) # Period is in microseconds

# Input: bytes of length 6 (representing: uint16 num, uint32 period)
# Return: BatchParams
def decode_batch_params(raw):
    num = decode_int(raw[0:2], signed=False)
    period = decode_int(raw[2:6], signed=False)/1000 # Conversion micros->millis
    return BatchParams(num, period)

# Input: bytes of length 8
# Return: 8x8 numpy array of uint8 (1 represents lit pixel)
# Each byte of input corresponds to column of output, with MSB at top of column
def decode_screen_tile(data):
    data = np.array([[elt] for elt in data[::-1]], dtype=np.uint8)
    tile = np.unpackbits(data, axis=1)
    return tile.transpose()

# Saves an objec to a file
def save(obj, filename):
    f = open(filename, 'wb')
    pickle.dump(obj,f)
    f.close()

# Loads an object from a file
def load(filename):
    f = open(filename, 'rb')
    obj = pickle.load(f)
    f.close()
    return obj