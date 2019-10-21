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

import argparse
import os
try:
  import simplejson as json
except ImportError:
  import json

from nab.corpus import Corpus
from nab.util import recur

"""
Create a json file containing an empty label for each datafile.
"""


def main(args):

  root = recur(os.path.dirname, os.path.realpath(__file__), n=2)

  if not os.path.isabs(args.labelFile):
    args.labelDir = os.path.join(root, args.labelFile)

  if not os.path.isabs(args.dataDir):
    args.dataDir = os.path.join(root, args.dataDir)

  corpus = Corpus(args.dataDir)

  empty_labels = {p : [] for p in list(corpus.dataFiles.keys()) if "Known" not in p}

  with open(args.labelFile, "w") as outFile:
    outFile.write(json.dumps(empty_labels,
             sort_keys=True, indent=4, separators=(',', ': ')))

  print("Empty label file written to",args.labelFile)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("--dataDir",
                    default="data",
                    help="Directory structure containing all the CSV "
                         "data files.")

  parser.add_argument("--labelFile",
                    default=os.path.join("labels","empty_labels.json"),
                    help="Filename containing the empty json labels file.")

  args = parser.parse_args()
  main(args)

