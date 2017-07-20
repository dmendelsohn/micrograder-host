import sys

from src import utils
from src.screen import Font
from src.utils import EventType
from src.utils import OutputType

# In the log, special print messages of one of the following formats:
# Font:<codepoint>,<x>,<y>,<width>,<height>
# At the time that message is received, the bitmap for the given codepoint
# will be saved (it's the box specified by the latter four numbers on the most
# recently received screen)
# For now, we expect all characters to have same width and height
def construct_font(log):
    last_screen = None
    bitmaps = {} # Map codepoint to 2D np array
    for request in log.requests:
        if request.is_output and request.data_type == OutputType.Screen:
            last_screen = request.values[0]
        elif request.is_event and request.data_type == EventType.Print:
            args = parse_print_message(request.arg)
            if args: # Rules out invalid or irrelevant print messages
                if last_screen: # Make sure we have a screen
                    (codepoint, x, y, width, height) = args # Unpack tuple
                    bitmaps[codepoint] = last_screen.get_box(x, y, width, height)

    shapes = set([bitmap.shape for bitmap in bitmaps.values()])
    if len(shapes) == 0:
        return None # No valid character bitmaps in the log
    elif len(shapes) > 1:
        print("Error: not all bitmaps are the same shape")
        sys.exit(1)
    else:
        height, width = list(shapes)[0] # Only element of shapes
        for codepoint in bitmaps: # Convert the bitmap to integer representation
            bitmaps[codepoint] = utils.bitmap_to_int(bitmaps[codepoint])
        return Font(width=width, height=height, chars=bitmaps)

# Returns the (codepoint, x, y, width, height) tuple, or None if ill-formated statement
def parse_print_message(text):
    if len(text) < 5 or text[:5] != "Font:":
        return None
    text = text[5:] # Just comma separated ints, we hope
    parts = text.split(",")
    if len(parts) != 5:
        return None
    try:
        return tuple(map(int, parts))
    except ValueError:
        return None