import numpy as np
from collections import namedtuple

ScreenShape = namedtuple('ScreenShape', ['width', 'height'])  # In pixels

# Note: 0, 0 is considered top-left corner
# Note: typically we'll talk in (x,y) coordinates, not (row, col)
class Screen:

    # Specify EITHER buff (2D numpy array) or both width and height
    # width and height are measured in pixels
    def __init__(self, buff=None, width=None, height=None):
        if buff is not None:
            self.buffer = np.copy(buff)
        else: # Assume width and height are provided
            self.buffer = np.zeros((height, width), dtype=np.uint8)

    # paint rect (2D numpy array) onto buffer with top-left corner at x, y
    # Later: make this handle out-of-bounds issues
    def paint(self, rect, x, y):
        self.buffer[y:y+rect.shape[0],x:x+rect.shape[1]] = rect

    def height(self):
        return self.buffer.shape[0]

    def width(self):
        return self.buffer.shape[1]

    def __eq__(self, other):
        return np.array_equal(self.buffer, other.buffer)

    def copy(self):
        return Screen(buff=self.buffer)

    # Later: lots of utility functions identifying features of buffer