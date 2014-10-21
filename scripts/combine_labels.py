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
import time
import pprint
import argparse

from nab.labeler import LabelCombiner, CorpusLabel
from nab.corpus import Corpus
from nab.util import recur, checkInputs

depth = 2

root = recur(os.path.dirname, os.path.realpath(__file__), depth)
print root


def main(args):
  if not args.absolutePaths:
    dataDir = os.path.join(root, args.dataDir)
    labelDir = os.path.join(root, args.labelDir)
  else:
    dataDir = args.dataDir
    labelDir = args.labelDir

  destPath = args.destPath
  threshold = int(args.threshold)

  print "Getting Corpus"

  corpus = Corpus(dataDir)

  print "Creating LabelCombiner"

  labelCombiner = LabelCombiner(labelDir, corpus, threshold)

  print "Combining Labels"

  labelCombiner.combine()

  print "Writing combined labels"

  labelCombiner.write(destPath)

  print "Attempting to load objects as a test"

  corpusLabel = CorpusLabel(path=destPath, corpus=corpus)

  print "Successfully combined labels"


  print "Resulting windows stored in:", destPath

  pprint.pprint(corpusLabel.windows)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("--labelDir",
                    help="This directory holds all the individual labels")

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus")

  parser.add_argument("--destPath",
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
    start = time.time()
    main(args)
    end = time.time()
    print "Elapsed time:", end - start

