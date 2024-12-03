#! /usr/bin/env python
# Copyright 2014-2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
"""
Combines a set of raw label files.
"""

import argparse
import os
import pprint
import time

from nab.corpus import Corpus
from nab.labeler import LabelCombiner, CorpusLabel
from nab.util import recur, checkInputs



def main(args):
  if not args.absolutePaths:
    root = recur(os.path.dirname, os.path.realpath(__file__), 2)
    dataDir = os.path.join(root, args.dataDir)
    labelDir = os.path.join(root, args.labelDir)
  else:
    dataDir = args.dataDir
    labelDir = args.labelDir

  # The following params are used in NAB scoring, but defined here because they
  # impact the labeling process -- i.e. windows cannot exist in the probationary
  # period.
  windowSize = 0.10
  probationaryPercent = 0.15


  print("Getting corpus.")
  corpus = Corpus(dataDir)

  print("Creating LabelCombiner.")
  labelCombiner = LabelCombiner(labelDir, corpus,
                                args.threshold, windowSize,
                                probationaryPercent, args.verbosity)

  print("Combining labels.")
  labelCombiner.combine()

  print("Writing combined labels files.")
  labelCombiner.write(args.combinedLabelsPath, args.combinedWindowsPath)

  print("Attempting to load objects as a test.")
  corpusLabel = CorpusLabel(args.combinedWindowsPath, corpus)
  corpusLabel.validateLabels()

  print("Successfully combined labels!")
  print("Resulting windows stored in:", args.combinedWindowsPath)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("--labelDir",
                      default="labels/raw",
                      help="This directory holds the individual label files")

  parser.add_argument("--dataDir",
                      default="data",
                      help="This holds all the data files for the corpus")

  parser.add_argument("--combinedLabelsPath",
                      default="labels/combined_labels.json",
                      help="Where the combined labels file will be stored")

  parser.add_argument("--combinedWindowsPath",
                      default="labels/combined_windows.json",
                      help="Where the combined windows file will be stored")

  parser.add_argument("--absolutePaths",
                      default=False,
                      action="store_true",
                      help="If specified, paths are absolute paths")

  parser.add_argument("--threshold",
                      default=0.5,
                      type=float,
                      help="The percentage agreement you would like between "
                           "all labelers for a record to be considered "
                           "anomalous.")
                      
  parser.add_argument("--verbosity",
                      default=1,
                      type=int,
                      help="Set the level of verbosity; to print out labeling "
                           "metrics during the process, acceptable values are "
                           "0, 1, and 2.")

  parser.add_argument("--skipConfirmation",
                    default=False,
                    action="store_true",
                    help="If specified will skip the user confirmation step")

  args = parser.parse_args()

  if args.skipConfirmation or checkInputs(args):
    main(args)
