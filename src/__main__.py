import argparse

from . import run
from . import utils

parser = argparse.ArgumentParser()
parser.add_argument("testcasepath", help="Path to test case file")
parser.add_argument("--logpath", help="Path to save log")
parser.add_argument("-r", "--run", help="Run session", action="store_true")
parser.add_argument("-e", "--evaluate", help="Evaluate log", action="store_true")
parser.add_argument("-v", "--verbose", help="Verbose printing", action="store_true")
parser.add_argument("-t", "--timeout", help="Request timeout in seconds", type=float)
args = parser.parse_args()

if args.run:
    log = run.main(args.testcasepath, args.logpath, verbose=args.verbose, timeout=args.timeout)
elif args.logpath is not None:
    log = utils.load(args.logpath)
else:
    log = None

if args.evaluate:
    if log is None:
        print("Error: no log to evalute")
    else:
        test_case = utils.load(args.testcasepath)
        results = test_case.evaluator.evaluate(log)
        print("Results: {}".format(results))


