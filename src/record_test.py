from . import utils
from .case import TestCase

#TODO: description
def record():
    # TODO: return some sort of log
    return None 

#TODO: description
def build_test_case(recording):
    # TODO: return a TestCase
    return None

def main(filepath):
    print("Record called with filepath={}".format(filepath))
    recording = record()
    case = build_test_case(recording)
    utils.save(case, filepath)