#! /usr/bin/env python
# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import os
import argparse
import pandas

from nab.corpus import Corpus
from nab.labeler import CorpusLabel
from nab.util import recur, checkInputs

depth = 2

root = recur(os.path.dirname, os.path.realpath(__file__), depth)



def main(args):

  if not args.absolutePaths:
    args.labelDir = os.path.join(root, args.labelDir)
    args.dataDir = os.path.join(root, args.dataDir)
    args.destDir = os.path.join(root, args.destDir)

  if not checkInputs(args):
    return

  corpus = Corpus(args.dataDir)

  corpusLabel = CorpusLabel(args.labelDir, corpus=corpus)
  corpusLabel.getEverything()

  columnData = {}
  for relativePath in list(corpusLabel.labels.keys()):
    columnData[relativePath] = pandas.Series(
      corpusLabel.labels[relativePath]["label"])

  corpus.addColumn("label", columnData)

  corpus.copy(newRoot=args.destDir)

  print("Done adding labels!")


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--labelDir",
                    default="labels",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--destDir",
                    help="Where you want to store the resulting corpus")

  parser.add_argument("--absolutePaths",
                      help="Whether file paths entered are not relative to \
                      NAB root",
                      default=False,
                      action="store_true")

  args = parser.parse_args()
  main(args)

