#! /usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
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


  print "Getting corpus."
  corpus = Corpus(dataDir)

  print "Creating LabelCombiner."
  labelCombiner = LabelCombiner(labelDir, corpus,
                                args.threshold, windowSize,
                                probationaryPercent, args.verbosity)

  print "Combining labels."
  labelCombiner.combine()

  print "Writing combined labels files."
  labelCombiner.write(args.combinedLabelsPath, args.combinedWindowsPath)

  print "Attempting to load objects as a test."
  corpusLabel = CorpusLabel(args.combinedWindowsPath, corpus)
  corpusLabel.validateLabels()

  print "Successfully combined labels!"
  print "Resulting windows stored in:", args.combinedWindowsPath


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
