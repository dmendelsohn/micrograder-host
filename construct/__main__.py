import argparse

from . import construct_test

parser = argparse.ArgumentParser()
parser.add_argument("--logpath", help="Path from which to load RequestLog")
parser.add_argument("--testcasepath", help="Path to save TestCase")
parser.add_argument("-v", "--verbose", help="Verbose printing", action="store_true")
parser.add_argument("-n", "--num", help="Number of frames (>0)", default=1, type=int)
args = parser.parse_args()

construct_test.main(logpath=args.logpath, testcasepath=args.testcasepath,
                    verbose=args.verbose, num_frames=args.num)
