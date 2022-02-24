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

import argparse
import os
try:
  import simplejson as json
except ImportError:
  import json

from nab.runner import Runner
from nab.util import (detectorNameToClass, checkInputs)



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
  windowsFile = os.path.join(root, args.windowsFile)
  resultsDir = os.path.join(root, args.resultsDir)
  profilesFile = os.path.join(root, args.profilesFile)
  thresholdsFile = os.path.join(root, args.thresholdsFile)

  runner = Runner(dataDir=dataDir,
                  labelPath=windowsFile,
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

  if args.normalize:
    try:
      runner.normalize()
    except AttributeError("Error: you must run the scoring step with the "
                          "normalization step."):
      return


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

  parser.add_argument("--normalize",
                    help="Normalize the final scores",
                    default=False,
                    action="store_true")

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
                    default=["null", "random",
                             "bayesChangePt", "windowedGaussian", "expose",
                             "relativeEntropy", "earthgeckoSkyline"],
                    help="Comma separated list of detector(s) to use, e.g. "
                         "null, expose")

  parser.add_argument("-p", "--profilesFile",
                    default=os.path.join("config", "profiles.json"),
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_argument("-t", "--thresholdsFile",
                    default=os.path.join("config", "thresholds.json"),
                    help="The configuration file that stores thresholds for "
                    "each combination of detector and username")

  parser.add_argument("-n", "--numCPUs",
                    default=None,
                    help="The number of CPUs to use to run the "
                    "benchmark. If not specified all CPUs will be used.")

  args = parser.parse_args()

  if (not args.detect
      and not args.optimize
      and not args.score
      and not args.normalize):
    args.detect = True
    args.optimize = True
    args.score = True
    args.normalize = True

  if len(args.detectors) == 1:
    # Handle comma-seperated list argument.
    args.detectors = args.detectors[0].split(",")

  # The following imports are necessary for getDetectorClassConstructors to
  # automatically figure out the detector classes.
  # Only import detectors if used so as to avoid unnecessary dependency.
  if "bayesChangePt" in args.detectors:
    from nab.detectors.bayes_changept.bayes_changept_detector import (
      BayesChangePtDetector)
  if "null" in args.detectors:
    from nab.detectors.null.null_detector import NullDetector
  if "random" in args.detectors:
    from nab.detectors.random.random_detector import RandomDetector
  # By default the skyline detector is disabled, it can still be added to the
  # detectors argument to enable it, for more info see #335 and #333
  if "skyline" in args.detectors:
    from nab.detectors.skyline.skyline_detector import SkylineDetector
  if "windowedGaussian" in args.detectors:
    from nab.detectors.gaussian.windowedGaussian_detector import (
      WindowedGaussianDetector)
  if "knncad" in args.detectors:
    from nab.detectors.knncad.knncad_detector import KnncadDetector
  if "relativeEntropy" in args.detectors:
    from nab.detectors.relative_entropy.relative_entropy_detector import (
      RelativeEntropyDetector)
  if "expose" in args.detectors:
    from nab.detectors.expose.expose_detector import ExposeDetector
  if "contextOSE" in args.detectors:
    from nab.detectors.context_ose.context_ose_detector import (
    ContextOSEDetector )
  if "earthgeckoSkyline" in args.detectors:
    from nab.detectors.earthgecko_skyline.earthgecko_skyline_detector import EarthgeckoSkylineDetector
  if "ARTime" in args.detectors:
    from nab.detectors.ARTime.ARTime_detector import ARTimeDetector

  if args.skipConfirmation or checkInputs(args):
    main(args)
