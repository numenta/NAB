#! /usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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

