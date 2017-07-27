from collections import namedtuple
import numpy as np
from PIL import Image
import pytesseract

# width and height are width and height of fixed-width font
# chars is map of codepoint to integer packing of bitmap
# integer packing is done column-by-column, MSB in top-left (i.e. lowest indices are MSB)
Font = namedtuple('Font', ['width','height', 'chars'])
DEFAULT_IGNORED_CHARS = set(["-","_", ",", ".", "\"", "\'", "|", "`"]) # These are a pain

ScreenShape = namedtuple('ScreenShape', ['width', 'height'])  # In pixels

# Note: 0, 0 is considered top-left corner
# Note: typically we'll talk in (x,y) coordinates, not (row, col)
class Screen:

    # Specify EITHER buff (2D numpy array) or both width and height
    # width and height are measured in pixels
    def __init__(self, buff=None, width=None, height=None):
        if buff is not None:
            self.buffer = np.copy(buff)
            self.shape = ScreenShape(width=buff.shape[1], height=buff.shape[0])
        else: # Assume width and height are provided
            self.buffer = np.zeros((height, width), dtype=np.uint8)
            self.shape = ScreenShape(width=width, height=height)

    # paint rect (2D numpy array) onto buffer with top-left corner at x, y
    # Later: make this handle out-of-bounds issues
    def paint(self, rect, x, y):
        self.buffer[y:y+rect.shape[0],x:x+rect.shape[1]] = rect

    def get_box(self, x, y, width, height):
        return self.buffer[y:y+height,x:x+width]

    def get_num_pixels_lit(self):
        return sum(sum(self.buffer))

    def height(self):
        return self.buffer.shape[0]

    def width(self):
        return self.buffer.shape[1]

    def __eq__(self, other):
        return type(other) is Screen and np.array_equal(self.buffer, other.buffer)

    def copy(self):
        return Screen(buff=self.buffer)

    def __repr__(self):
        return repr(self.buffer)

    def describe2(self):
        #TODO: implement
        pass


    # Extracts text out of the buffer, using a given monospace font (basically, a set of bitmaps)
    # font: namedtuple Font (see above)
    # ignored_chars: set of characters to ignore.  If None, defaults are used.
    # line_delimeter: character inserted between lines
    # Note that lines can overlap in height.  Also, whitespace is stripped off start and end
    # of each line, and whitespace within a single line is reduced to a single space
    def extract_text(self, font, *, ignored_chars=None, line_delimeter='\n'):
        if ignored_chars is None:
            ignored_chars = DEFAULT_IGNORED_CHARS
        lut = {}
        for (key, val) in font.chars.items():
            lut[val] = key # Inverted chars dictionary
        labels = self.get_box_values(font.width, font.height)
        text = ""
        for row in labels:
            line = ""
            for elt in row:
                if elt in lut:
                    char = chr(lut[elt])
                    if char not in ignored_chars:
                        line += char
            line = line.strip() # Remove leading and trailing whitespace
            if " " in ignored_chars:
                line = "".join(line.split()) # Remove internal whitespace entirely
            else:
                line = " ".join(line.split()) # Remove duplicate internal spaces
            if len(line) > 0:
                text += line
                if line_delimeter:
                    text += line_delimeter
        return text.strip() # strip removes trailing newline

    # Return 2D list of same shape as buffer, elements are ints
    # Each element in the "box value" of the box with top-left corner at that position
    # "box value" is bit packing, column by column, with MSB in top-left
    # Takes about 20ms on a 128x64 screen with a 5x7 box
    def get_box_values(self, box_width, box_height):
        labels = [[0 for x in range(self.shape.width)] for y in range(self.shape.height)]

        # First, make each elt of labels the "column" hash for the box column rooted there
        for x in range(self.shape.width):
            rolling_sum = 0
            for y in range(self.shape.height + box_height - 1):
                rolling_sum = (rolling_sum << 1)%(2**box_height)
                if y < self.shape.height:
                    rolling_sum += self.buffer[y,x]
                if y >= box_height-1:
                    labels[y-box_height+1][x] = rolling_sum

        # Second, sum across the rows to make each label the total "box" hash
        for y in range(self.shape.height):
            rolling_sum = 0
            for x in range(self.shape.width + box_width - 1):
                rolling_sum = (rolling_sum << box_height)%(2**(box_height*box_width))
                if x < self.shape.width:
                    rolling_sum += labels[y][x]
                if x >= box_width-1:
                    labels[y][x-box_width+1] = rolling_sum

        return labels

    # Returns number of matching pixels between this screen's buffer and another screen's buffer
    # left, right, up, and down are all allowabled shifts of the other screen to get the best match
    # Empty space due to a shift is filled with 0s
    # If shift (an int) is provided, that overrides all of left, right, up, and down
    def get_num_matching_pixels(self, other, *, shift=None, left=0, right=0, up=0, down=0):
        if shift is not None:
            left = right = up = down = shift

        if type(other) is not Screen or self.shape != other.shape:
            raise ValueError("Invalid argument: other={}".format(other))

        padded_buffer = np.zeros((self.height()+up+down, self.width()+right+left), dtype=np.uint8)
        padded_buffer[up:up+self.height(),left:left+self.width()] = self.buffer

        best = 0
        for x_shift in range(-left,right+1):
            for y_shift in range(-up,down+1):
                x_min = x_shift + left
                x_max = x_min + self.width()
                y_min = y_shift + up
                y_max = y_min + self.height()
                diff = np.mod(padded_buffer[y_min:y_max, x_min:x_max] + other.buffer, 2) # XOR
                num_matching_pixels = self.width() * self.height() - sum(sum(diff))
                if num_matching_pixels > best:
                    best = num_matching_pixels

        return best


# Returns a function, f, that takes in two Screens
#   f returns True if num matching pixels is >= num, False otherwise
#   f raises ValueError if screens are not same shape
# Usage of other arguments is same as Screen.get_num_matching_pixels, directions
# refer to movement of second Screen relative to first.
def pixel_match_min(num, *, shift=None, left=0, right=0, up=0, down=0):
    def f(expected, actual):
        matches = expected.get_num_matching_pixels(actual, shift=shift, left=left, up=up, down=down)
        return (matches >= num)
    return f

# Complement of the above function, f returns True if num errors <= num
def pixel_error_max(num, *, shift=None, left=0, right=0, up=0, down=0):
    def f(expected, actual):
        matches = expected.get_num_matching_pixels(actual, shift=shift, left=left, up=up, down=down)
        errors = expected.height()*expected.width() - matches
        return (errors <= num)
    return f

# This function is a nice one for comparing screen closeness.  Like the ones above, it
# returns a function, f, that takes in two Screens and outputs a boolean.  The function returns
# True if a sufficient number of pixels match.  That cutoff is dynamically chosen as a number
# between the number of unlit pixels in the first Screen, and the total Screen size, and the input
# ratio determines the fraction of the way from the former to the latter.  That is, a ratio of 0 would
# allow f to return True if the second Screen is blank, and a ratio of 1 requires the two Screens
# are perfect matches
def relatively_close(ratio, *, shift=None, left=0, right=0, up=0, down=0):
    def f(expected, actual):
        expected_lit = sum(sum(expected.buffer))
        expected_off = expected.width() * expected.height() - expected_lit
        cutoff = expected_off + ratio*expected_lit
        matches = expected.get_num_matching_pixels(actual, shift=shift, left=left, up=up, down=down)
        return (matches >= cutoff)
    return f





