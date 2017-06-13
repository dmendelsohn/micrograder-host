import numpy as np

# Note: 0, 0 is considered top-left corner
# Note: typically we'll talk in (x,y) coordinates, not (row, col)
class Screen:
    
    # Specify EITHER buff (2D numpy array) or both width and height
    # width and height are measured in pixels
    def __init__(self, buff=None, width=None, height=None):
        if buff is not None:
            self.buffer = buff
        else: # Assume width and height are provided
            self.buffer = np.zeros((height, width), dtype=np.uint8)

    # paint rect (2D numpy array) onto buffer with top-left corner at x, y
    def paint(self, rect, x, y):
        self.buffer[y:y+rect.shape[0],x:x+x.shape[1]] = rect

    def height(self):
        return self.buffer.shape[0]

    def width(self):
        return self.buffer.shape[1]

    # Later: lots of utility functions identifying features of buffer