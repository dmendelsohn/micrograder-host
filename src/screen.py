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

    def get_image(self):
        def lut(val):
            if val:
                return 255
            else:
                return 0
        return Image.fromarray(self.buffer).point(lut, mode="1")

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
            if "_" in ignored_chars:
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
