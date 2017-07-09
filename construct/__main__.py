import argparse
import sys

from . import construct_test
from src import utils

parser = argparse.ArgumentParser()
parser.add_argument("--log", help="Path from which to load RequestLog")
parser.add_argument("--testcase", help="Path to save TestCase")
parser.add_argument("-v", "--verbose", help="Verbose printing", action="store_true")
parser.add_argument("-n", "--num", help="Number of frames (>0)", default=1, type=int)
args = parser.parse_args()

if args.log is None:
    construct_test.construct_hardcode()
    sys.exit(0)

if args.testcase is None:
    print("Error: Please provide path to save test case with --testcase option")
    sys.exit(1)

log = utils.load(args.log)
scaffold = construct_test.default_scaffold(args.num)
testcase = construct_test.construct_dynamic(log, scaffold)
utils.save(testcase, args.testcase)