#! /usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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
