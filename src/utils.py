from collections import namedtuple
import dill as pickle
from enum import Enum
import numpy as np
import operator
import struct

MILLISECOND = 1 # time unit(s) per millisecond
RESULTS_DIR = "results"

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


# Returns a string description of the data_type/channel
# TODO: add config dict {(data_type, channel)->str}
def describe_channel(data_type, channel=None):
    # Defaults
    if data_type == OutputType.DigitalWrite:
        if channel is None:
            raise ValueError("DigitalWrite must have a channel (pin number)")
        return "Digital pin {}".format(channel)
    elif data_type == OutputType.AnalogWrite:
        if channel is None:
            raise ValueError("AnalogWrite must have a channel (pin number)")
        return "Analog pin {}".format(channel)
    elif data_type == OutputType.Screen: # Ignore channel
        return "Screen"
    elif data_type == EventType.Print: # Ignore channel
        return "Print"
    else:
        desc = str(data_type)
        if channel is not None:
            desc += " {}".format(channel)
        return desc

# Used to get reduced descriptions (not necessarily str) of an object
# e.g. especially useful for Screens and stuff
# By default, object itself is returned
# This function looks for an attribute called "description", then
# a method called "describe()", and then default
def get_description(obj, default=None):
    if hasattr(obj, "description"):
        return obj.description
    elif callable(getattr(obj, "describe", None)):
        return obj.describe()
    else:
        return default

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

# Returns int representation of binary 2D numpy array (i.e. packs the bits)
# bits are packed by column, MSB in top-left corner (i.e. location (0,0))
def bitmap_to_int(bitmap):
    height, width = bitmap.shape
    num = 0
    for x in range(width):
        for y in range(height):
            num = (num << 1) + bitmap[y,x]
    return num

# Inverse of the above function, returns a binary 2D numpy array
def int_to_bitmap(num, width, height):
    bitmap = np.zeros((height,width), dtype=np.uint8)
    for x in range(width-1, -1, -1):
        for y in range(height-1, -1, -1):
            bitmap[y,x] = num%2
            num >>= 1
    return bitmap

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