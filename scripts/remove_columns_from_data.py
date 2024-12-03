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

from nab.corpus import Corpus
from nab.util import recur

depth = 3

root = recur(os.path.dirname, os.path.realpath(__file__), depth)



def main(args):
  if not args.absolutePaths:
    args.dataDir = os.path.join(root, args.dataDir)
    if args.destDir:
      args.destDir = os.path.join(root, args.destDir)

  corpus = Corpus(args.dataDir)

  for name in args.columnNames:
    corpus.removeColumn(name, write=True, newRoot=args.destDir)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--destDir",
                    default=None,
                    help="Where you want to store the resulting corpus")

  parser.add_argument("--absolutePaths",
                      help="Whether file paths entered are not relative to \
                      NAB root",
                      default=False,
                      action="store_true")

  parser.add_argument("--columnNames",
                      help="All the names of the columns which must be removed",
                      nargs="+",
                      type=str)

  args = parser.parse_args()
  main(args)
