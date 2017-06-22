import argparse

from . import construct_test
from . import record_test
from . import run_test

parser = argparse.ArgumentParser()
parser.add_argument("mode", help="either 'record' or 'run' or 'construct")
parser.add_argument("-f", "--filepath", help="path to relevant test_case file")
args = parser.parse_args()

if args.mode == "record":
    record_test.main(args.filepath)
elif args.mode == "run":
    run_test.main(args.filepath)
elif args.mode == "construct":
    construct_test.main() # No argument
else:
    print("Invalid mode: {}".format(args.mode))
