import argparse
import os
import pprint
import shutil
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

def require(field):
    if not hasattr(args, field):
        print("Error: Please provide path to file with --{} option".format(field))
        sys.exit(1)

# Saves results of a test in results directory
def save_results(description, brief_description, images):
    results_dir = utils.RESULTS_DIR
    if os.path.exists(results_dir):
        if os.path.isdir(results_dir):
            shutil.rmtree(results_dir) # Remove directory and all contents
        else:
            os.remove(results_dir) # It's a regular file, remove it

    os.mkdir(results_dir) # Make new directory
    with open(results_dir + "/description.txt", "w") as f:
        pprint.pprint(description, f)
    with open(results_dir + "/brief_description.txt", "w") as f:
        pprint.pprint(brief_description, f)

    if images:
        os.mkdir(results_dir + "/images")
        num_digits = len(str(len(images)-1))
        for i in range(len(images)):
            filename = results_dir + "/images/image{:0" + str(num_digits) + "d}.png"
            filename = filename.format(i)
            images[i].save(filename)

def assess_log(evaluator, log):
    results = evaluator.evaluate(log)
    description = evaluator.describe(results)
    images = evaluator.replace_images(description)
    brief_description = evaluator.brief_description(description)
    save_results(description, brief_description, images)

if args.mode == "assess":
    require("testcase")

    testcase = utils.load(args.testcase)
    log = run.run_session(testcase.handler, verbose=args.verbose)
    if args.log is not None: # Save at that path
        utils.save(log, args.log)

    assess_log(testcase.evaluator, log)
    

elif args.mode == "assess_log":
    require("testcase")
    require("log")

    evaluator = utils.load(args.testcase).evaluator
    log = utils.load(args.log)

    assess_log(evaluator, log)

elif args.mode == "record":
    handler = RequestHandler() # Blank, endless handler
    log = run.run_session(handler, verbose=args.verbose)

    path = args.log
    if path is None:
        path = "./temp.log"

    print("Saving recording to {}".format(path))
    utils.save(log, path)

else:
    print("Invalid mode: use 'assess' or 'record' or 'assess_log'")