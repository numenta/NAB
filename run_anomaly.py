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
import sys
import yaml

from optparse import OptionParser

from detectors import (NumentaDetector, SkylineDetector)

def runAnomaly(options):
  """
  Run selected detector on selected file
  """

  # Load the config file
  with open(options.config) as configHandle:
    config = yaml.load(configHandle)

  outputDir = getOutputDir(options)

  # Align our initial window from which we are allowed to collect statistics
  # with the window in which detectors will not return any results.
  probationaryPeriod = config['ProbationaryPeriod']

  # If the detector is 'detector', the detector class must be named
  # DetectorDetector
  detector = options.detector[0].upper() + options.detector[1:]
  className = detector + "Detector"
  if className not in globals():
    print("ERROR: The provided detector was not recognized. Please add a class "
          "in the detectors/ dir. Add that class to the detectors/__init__.py "
          "file and finally add that class to the list of detectors imported "
          "in this file. ... Sorry!")
    sys.exit(1)
  else:
    detectorClass = globals()[className](probationaryPeriod,
                                          options.inputFile,
                                          outputDir)
  try:
    detectorClass.run()
  except RuntimeError, e:
    print "Error: %s" % (e)

def getOutputDir(options):
  """
  Return the directory into which we should place results file based on
  input options.

  This will also *create* that directory if it does not already exist.
  """

  base = options.outputDir
  detectorDir = options.detector
  if options.inputFile:
    dataGroupDir = osPathSplit(options.inputFile)[1]
  else:
    print "ERROR: You must specify an --inputFile"
    sys.exit(1)
  outputDir = os.path.join(base, detectorDir, dataGroupDir)

  if not os.path.exists(outputDir):
    # This is being run in parralel so watch out for race condition.
    try:
      os.makedirs(outputDir)
    except OSError:
      pass

  return outputDir

def osPathSplit(path, debug=False):
  """
  os_path_split_asunder
  http://stackoverflow.com/questions/4579908/cross-platform-splitting-of-path-in-python
  """
  parts = []
  while True:
    newpath, tail = os.path.split(path)
    if debug:
      print repr(path), (newpath, tail)
    if newpath == path:
      assert not tail
      if path:
        parts.append(path)
      break
    parts.append(tail)
    path = newpath
  parts.reverse()
  return parts


#############################################################################

if __name__ == "__main__":

  usage = "usage: %prog --inputFile <path_to/file.csv> [options]"

  # All the command line options
  parser = OptionParser(usage)
  parser.add_option("-i", "--inputFile",
                    help="Path to data file. (REQUIRED)",
                    dest="inputFile", default=None)
  parser.add_option("--outputDir",
                    help="Output Directory. Results files will be place here.",
                    dest="outputDir", default="results/")
  parser.add_option("-d", "--detector",
                    help="Which Anomaly Detector class to use.",
                    default="numenta")
  parser.add_option("--config", default="benchmark_config.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")
  parser.add_option("--verbosity", default=0, help="Increase the amount and "
                    "detail of output by setting this greater than 0.")

  options, args = parser.parse_args(sys.argv[1:])

  if not options.inputFile:
    parser.print_help()
    sys.exit(1)

  # Run it
  runAnomaly(options)



