import argparse

from . import construct_test

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Verbose printing", action="store_true")
args = parser.parse_args()

construct_test.main(verbose=args.verbose)
