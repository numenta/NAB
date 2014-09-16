#!/usr/bin/env python
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
import argparse
import yaml
from nab.lib.running import Runner
from nab.lib.util import (recur,
                         detectorNameToClass,
                         checkInputs,
                         updateThresholds)

from nab.detectors.numenta.numenta_detector import NumentaDetector
from nab.detectors.skyline.skyline_detector import SkylineDetector

depth = 2

root = recur(os.path.dirname, os.path.realpath(__file__), depth)



def main(args):

  if not args.detect and not args.score and not args.optimize:
    args.detect = True
    args.optimize = True
    args.score = True

  args.dataDir = os.path.join(root, args.dataDir)
  args.labelDir = os.path.join(root, args.labelDir)
  args.resultsDir = os.path.join(root, args.resultsDir)
  args.profilesPath = os.path.join(root, args.profilesPath)
  args.thresholdPath = os.path.join(root, args.thresholdPath)

  runner = Runner(args)
  runner.initialize()

  if args.detect:
    detectorConstructors = getDetectorClassConstructors(args.detectors)
    runner.detect(detectorConstructors)

  if args.optimize:
    detectorThresholds = runner.optimize_threshold(args.detectors)
    detectorThresholds = updateThresholds(detectorThresholds, args.thresholdPath)
  else:
    with open(args.thresholdPath) as thresholdConfigFile:
      detectorThresholds = yaml.load(thresholdConfigFile)

  if args.score:
    print detectorThresholds
    runner.score(args.detectors, detectorThresholds)


def getDetectorClassConstructors(detectors):
  detectorConstructors = {d:globals()[detectorNameToClass(d)] for d in detectors}

  return detectorConstructors

if __name__ == "__main__":

  parser = argparse.ArgumentParser()

  parser.add_argument("--detect",
                    help="Generate detector results but do not analyze results \
                    files.",
                    default=False,
                    action="store_true")

  parser.add_argument("--score",
                    help="Analyze results in the results directory",
                    default=False,
                    action="store_true")

  parser.add_argument("--optimize",
                    help="Optimize the thresholds for each detector and user \
                    profile combination",
                    default=False,
                    action="store_true")

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--labelDir",
                    default="labels",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--resultsDir",
                    default="results",
                    help="This will hold the results after running detectors \
                    on the data")

  parser.add_argument("-d", "--detectors",
                    nargs="*",
                    type=str,
                    default=["numenta"],
                    help="Select which detector/detector(s) you want to use. \
                    Make sure to import the corresponding detectors classes \
                    within run.py")

  parser.add_argument("-p", "--profilesPath",
                    default="config/user_profiles.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_argument("-t", "--thresholdPath",
                    default="config/threshold_config.yaml",
                    help="The configuration file that stores thresholds for \
                    each combination of detector and username")

  parser.add_argument("-n", "--numCPUs",
                    default=None,
                    help="The number of CPUs to use to run the "
                    "benchmark. If not specified all CPUs will be used.")

  parser.add_argument("-pp","--probationaryPercent",
                    default=0.1,
                    help="The percentage of dataset to be used to configure \
                    the detector and not to be used for scoring")

  args = parser.parse_args()

  if checkInputs(args):
    main(args)
