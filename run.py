#!/usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
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

import argparse
import os
try:
  import simplejson as json
except ImportError:
  import json

from nab.runner import Runner
from nab.util import (detectorNameToClass, checkInputs)

# The following imports are necessary for getDetectorClassConstructors to
# automatically figure out the detector classes
from nab.detectors.numenta.numenta_detector import NumentaDetector
from nab.detectors.skyline.skyline_detector import SkylineDetector
from nab.detectors.random.random_detector import RandomDetector



def getDetectorClassConstructors(detectors):
  """
  Takes in names of detectors. Collects class names that correspond to those
  detectors and returns them in a dict. The dict maps detector name to class
  names. Assumes the detectors have been imported.
  """
  detectorConstructors = {
  d : globals()[detectorNameToClass(d)] for d in detectors}

  return detectorConstructors


def main(args):
  
  root = os.path.dirname(os.path.realpath(__file__))

  numCPUs = int(args.numCPUs) if args.numCPUs is not None else None

  dataDir = os.path.join(root, args.dataDir)
  labelFile = os.path.join(root, args.labelFile)
  resultsDir = os.path.join(root, args.resultsDir)
  profilesFile = os.path.join(root, args.profilesFile)
  thresholdsFile = os.path.join(root, args.thresholdsFile)
  
  runner = Runner(dataDir=dataDir,
                  labelPath=labelFile,
                  resultsDir=resultsDir,
                  profilesPath=profilesFile,
                  thresholdPath=thresholdsFile,
                  numCPUs=numCPUs)

  runner.initialize()

  if args.detect:
    detectorConstructors = getDetectorClassConstructors(args.detectors)
    runner.detect(detectorConstructors)

  if args.optimize:
    runner.optimize(args.detectors)

  if args.score:
    with open(args.thresholdsFile) as thresholdConfigFile:
      detectorThresholds = json.load(thresholdConfigFile)

    runner.score(args.detectors, detectorThresholds)


if __name__ == "__main__":

  parser = argparse.ArgumentParser()

  parser.add_argument("--detect",
                    help="Generate detector results but do not analyze results "
                    "files.",
                    default=False,
                    action="store_true")

  parser.add_argument("--optimize",
                    help="Optimize the thresholds for each detector and user "
                    "profile combination",
                    default=False,
                    action="store_true")

  parser.add_argument("--score",
                    help="Analyze results in the results directory",
                    default=False,
                    action="store_true")

  parser.add_argument("--skipConfirmation",
                    help="If specified will skip the user confirmation step",
                    default=False,
                    action="store_true")

  parser.add_argument("-d", "--detectors",
                    nargs="*",
                    type=str,
                    default=["numenta", "random", "skyline"],
                    help="Space separated list of detector(s) to use.")

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--resultsDir",
                    default="results",
                    help="This will hold the results after running detectors "
                    "on the data")

  parser.add_argument("--labelFile",
                    default=os.path.join("labels", "combined_labels.json"),
                    help="JSON file containing ground truth labels for the "
                         "corpus.")

  parser.add_argument("-p", "--profilesFile",
                    default="config/profiles.json",
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_argument("-t", "--thresholdsFile",
                    default="config/thresholds.json",
                    help="The configuration file that stores thresholds for "
                    "each combination of detector and username")

  parser.add_argument("-n", "--numCPUs",
                    default=None,
                    help="The number of CPUs to use to run the "
                    "benchmark. If not specified all CPUs will be used.")

  args = parser.parse_args()
  
  if not args.detect and not args.score and not args.optimize:
    args.detect = True
    args.optimize = True
    args.score = True

  if args.skipConfirmation or checkInputs(args):
    main(args)
