#!/usr/bin/env python
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

"""
Entry point for the Python 2 based detectors `numenta` and `numenta_tm`
"""
import argparse
import os
try:
  import simplejson as json
except ImportError:
  import json

from nab.runner import Runner
from nab.util import (detectorNameToClass, checkInputs)
from nab.detectors.numenta.numenta_detector import NumentaDetector
from nab.detectors.numenta.numentaTM_detector import NumentaTMDetector


def getDetectorClassConstructors(detectors):
  """
  Takes in names of detectors. Collects class names that correspond to those
  detectors and returns them in a dict. The dict maps detector name to class
  names. Assumes the detectors have been imported.
  """
  detectorConstructors = {
  d : globals()[detectorNameToClass(d)] for d in detectors}

  return detectorConstructors


def get_nth_parent_dir(n, path):
  """
  Return the Nth parent of `path` where the 0th parent is the direct parent
  directory.
  """
  parent = os.path.dirname(path)
  if n == 0:
    return parent

  return get_nth_parent_dir(n-1, parent)

def main(args):

  filepath = os.path.realpath(__file__)

  # Find the main NAB folder
  # Assuming `filepath` is ~ <...>/NAB/nab/detectors/numenta/run.py
  root = get_nth_parent_dir(3, filepath)

  numCPUs = int(args.numCPUs) if args.numCPUs is not None else None

  dataDir = os.path.join(root, args.dataDir)
  windowsFile = os.path.join(root, args.windowsFile)
  resultsDir = os.path.join(root, args.resultsDir)
  profilesFile = os.path.join(root, args.profilesFile)

  runner = Runner(dataDir=dataDir,
                  labelPath=windowsFile,
                  resultsDir=resultsDir,
                  profilesPath=profilesFile,
                  numCPUs=numCPUs)

  runner.initialize()

  detectorConstructors = getDetectorClassConstructors(args.detectors)
  runner.detect(detectorConstructors)


if __name__ == "__main__":

  parser = argparse.ArgumentParser()

  parser.add_argument("--skipConfirmation",
                    help="If specified will skip the user confirmation step",
                    default=False,
                    action="store_true")

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--resultsDir",
                    default="results",
                    help="This will hold the results after running detectors "
                    "on the data")

  parser.add_argument("--windowsFile",
                    default=os.path.join("labels", "combined_windows.json"),
                    help="JSON file containing ground truth labels for the "
                         "corpus.")

  parser.add_argument("-d", "--detectors",
                    nargs="*",
                    type=str,
                    default=["numenta", "numentaTM"],
                    help="Comma separated list of detector(s) to use")

  parser.add_argument("-p", "--profilesFile",
                    default=os.path.join("config", "profiles.json"),
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_argument("-n", "--numCPUs",
                    default=None,
                    help="The number of CPUs to use to run the "
                    "benchmark. If not specified all CPUs will be used.")

  # In this version of run.py this is a no-op
  # See https://github.com/numenta/NAB/issues/346 for why it was retained
  parser.add_argument("--detect",
                  help="No-op. See: https://github.com/numenta/NAB/issues/346",
                  default=False,
                  action="store_true")


  args = parser.parse_args()

  if len(args.detectors) == 1:
    # Handle comma-seperated list argument.
    args.detectors = args.detectors[0].split(",")

  if args.skipConfirmation or checkInputs(args):
    main(args)
