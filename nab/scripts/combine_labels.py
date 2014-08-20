#!/usr/bin/env python



import os
from os.path import dirname, realpath
import argparse

from nab.lib.labeling import LabelCombiner, CorpusLabel

from nab.lib.util import recur

depth = 3

root = recur(dirname, realpath(__file__), depth)

def main(args):
  if not args.absolutePaths:
    args.labelDir = os.path.join(root, args.labelDir)
    args.dataDir = os.path.join(root, args.dataDir)
    args.destDir = os.path.join(root, args.destDir)

  params = [args.labelDir, args.dataDir]

  if hasattr(args, "threshold"):
    params.append(args.threshold)

  print "Labels Directory: %s" % args.labelDir
  print "Data Directory: %s" % args.dataDir
  print "Destination Directory: %s" % args.destDir

  labelCombiner = LabelCombiner(*tuple(params))

  print "Combining Labels"

  labelCombiner.combine()

  print "Writing combined labels"

  labelCombiner.write(args.destDir)

  print "Attempting to load objects as a test"

  corpusLabel = CorpusLabel(args.destDir, args.dataDir)

  corpusLabel.getEverything()

  print "Success!"


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("--labelDir",
                    help="This directory holds all the individual labels")

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus")

  parser.add_argument("--destDir",
                    help="Where you want to store the combined labels",
                    default="labels",
                    action="store_true")

  parser.add_argument("--absolutePaths",
                      help="Whether file paths entered are not relative to \
                      NAB root",
                      default=False,
                      action="store_true")

  args = parser.parse_args()

  main(args)

