#! /usr/bin/env python
# Copyright 2014-2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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

