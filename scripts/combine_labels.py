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


import os
from os.path import dirname, realpath
import argparse

from nab.labeler import LabelCombiner, CorpusLabel

from nab.util import recur

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
                    default="labels")

  parser.add_argument("--absolutePaths",
                      help="Whether file paths entered are not relative to \
                      NAB root",
                      default=False,
                      action="store_true")

  args = parser.parse_args()

  main(args)

