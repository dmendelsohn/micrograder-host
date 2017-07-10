import argparse
import sys

from . import run
from . import utils
from .handler import RequestHandler



parser = argparse.ArgumentParser()
parser.add_argument("mode", help="Either 'assess' or 'record'")
parser.add_argument("--testcase", help="Path to test case file")
parser.add_argument("--log", help="Path to save log")
parser.add_argument("-v", "--verbose", help="Verbose printing", action="store_true")
args = parser.parse_args()



if args.mode == "assess":
    if args.testcase is None:
        print("Error: Please provide path to the .tc file with --testcase option")
        sys.exit(1)

    testcase = utils.load(args.testcase)
    log = run.run_session(testcase.handler, verbose=args.verbose)

    if args.log is not None: # Save at that path
        utils.save(log, args.log)

    results = testcase.evaluator.evaluate(log)
    print("Results: {}".format(results))

elif args.mode == "record":
    handler = RequestHandler() # Blank, endless handler
    log = run.run_session(handler, verbose=args.verbose)

    if args.log is not None: # Save at that path
        path = args.log
    else:
        path = "./temp.log"

    print("Saving recording to {}".format(path))
    utils.save(log, path)

else:
    print("Invalid mode: use 'assess' or 'record'")