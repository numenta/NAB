#! /usr/bin/env python
# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Prepares NAB for a new detector."""

import argparse
import os

from nab.util import getOldDict, recur, writeJSON

try:
  import simplejson as json
except ImportError:
  import json


def createThresholds(detectorName, thresholdFile):
  """"Create an entry in the threshold file for the new detector."""

  oldThresholds = getOldDict(thresholdFile)

  if detectorName not in oldThresholds:
    oldThresholds[detectorName] = {}

  writeJSON(thresholdFile, oldThresholds)


def createResultsDir(detectorName, resultsDir, categorySubDirs):
  """Create a results dir for the new detector with categorical subdirs."""

  directory = os.path.join(resultsDir, detectorName)

  if not os.path.exists(directory):
    os.makedirs(directory)

  for category in categorySubDirs:
    subdir = os.path.join(directory, category)
    if not os.path.exists(subdir):
      os.makedirs(subdir)


def getCategoryNames(dataDir, root):
  """Return a list of the names of data categories based on data subdirs."""

  return [d for d in next(os.walk(dataDir))[1]]


def main(args):

  if not args.detector:
    raise ValueError("Must specify detector name (--detector).")

  root = recur(os.path.dirname, os.path.realpath(__file__), 2)
  thresholdFile = os.path.join(root, args.thresholdFile)
  resultsDir = os.path.join(root, args.resultsDir)

  categorySubDirs = getCategoryNames(args.dataDir, root)

  createThresholds(args.detector, thresholdFile)
  
  createResultsDir(args.detector, resultsDir, categorySubDirs)



if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("--detector",
                      help="The name of the new detector to be added.")

  parser.add_argument("--resultsDir",
                      default="results",
                      help="This holds the path of the results directory.")

  parser.add_argument("--dataDir",
                      default="data",
                      help="This holds the path of the data directory.")

  parser.add_argument("--thresholdFile",
                      default="config/thresholds.json",
                      help="This holds the file path of the thresholds file.")

  args = parser.parse_args()
  main(args)

