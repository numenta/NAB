#! /usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
"""
Combines a set of labels given within folder (in the yaml format)
"""

import os
from os.path import dirname, realpath
import argparse

from nab.labeler import LabelCombiner, CorpusLabel

from nab.util import recur, checkInputs

depth = 2

root = recur(dirname, realpath(__file__), depth)

def main(args):
  if not args.absolutePaths:
    dataDir = os.path.join(root, args.dataDir)
  else:
    dataDir = args.dataDir

  destDir = args.destDir
  labelDir = args.labelDir
  threshold = args.threshold

  labelCombiner = LabelCombiner(labelDir, dataDir, threshold)

  print "Combining Labels"

  labelCombiner.combine()

  print "Writing combined labels"

  labelCombiner.write(destDir)

  print "Attempting to load objects as a test"

  corpusLabel = CorpusLabel(destDir, dataDir)

  corpusLabel.initialize()

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
                    default="labels")

  parser.add_argument("--absolutePaths",
                      help="Whether file paths entered are not relative to \
                      NAB root",
                      default=False,
                      action="store_true")

  parser.add_argument("--threshold",
                      help="The percentage agreement you would like between all\
                      labelers for a record to be considered anomalous (should \
                      be a number between 0 and 1)",
                      default=1.0)

  args = parser.parse_args()

  if checkInputs(args):
    main(args)

