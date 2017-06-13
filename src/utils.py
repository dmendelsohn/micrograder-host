class Test:
    # TODO: implement as iterable of Frames along with output log
    pass

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
        raise ValueError('Invalid encode width={} bytes with signed = {}'.format(width, signed))

