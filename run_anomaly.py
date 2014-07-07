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
import csv
import datetime
import dateutil.parser
import simplejson as json

from optparse import OptionParser
from pprint import pprint

from detectors import (GrokDetector, SkylineDetector)

def runAnomaly(options):
  """
  Run selected detector on selected file
  """

  outputDir = getOutputDir(options)

  # Align our initial window from which we are allowed to collect statistics
  # with the window in which detectors will not return any results.
  probationaryPeriod = 600

  # Grok Detector
  if options.detector == "grok":

    # Instantiate our detector
    grokDetector = GrokDetector(probationaryPeriod
                                options.inputFile,
                                outputDir)
    grokDetector.run()

  # SKYLINE detector
  elif options.detector == "skyline":

    etsyDetector = SkylineDetector(probationaryPeriod,
                                   options.inputFile,
                                   outputDir)
    etsyDetector.run()

  # ADD ADITIONAL DETECTORS HERE


  else:
    raise Exception("'%s' is not a recognized detector type." %
                    options.detector)

def getOutputDir(options):
  """
  Return the directory into which we should place results file based on
  input options.

  This will also *create* that directory if it does not already exist.
  """

  base = options.outputDir
  detectorDir = options.detector
  if options.inputFile:
    dataGroupDir = os_path_split_asunder(options.inputFile)[1]
  else:
    print("ERROR: You must specify an --inputFile")
    sys.exit(1)
  outputDir = os.path.join(base, detectorDir, dataGroupDir)

  if not os.path.exists(outputDir):
    # This is being run in parralel so watch out for race condition.
    try:
      os.makedirs(outputDir)
    except OSError:
      pass

  return outputDir

def os_path_split_asunder(path, debug=False):
  """
  From http://stackoverflow.com/questions/4579908/cross-platform-splitting-of-path-in-python
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
  parser.add_option("--inputFile",
                    help="Path to data file. (REQUIRED)", 
                    dest="inputFile", default=None)
  parser.add_option("--outputDir",
                    help="Output Directory. Results files will be place here.",
                    dest="outputDir", default="results/grok")
  parser.add_option("--max", default=None,
      help="Maximum number for the value field. If not set this value will be "
          "calculated from the inputFile data.")
  parser.add_option("--min", default=None,
      help="Minimum number for the value field. If not set this value will be "
          "calculated from the inputFile data.")
  parser.add_option("--verbosity", default=0, help="Increase the amount and "
                    "detail of output by setting this greater than 0.")
  parser.add_option("--detector", help="Which Anomaly Detector class to use.",
                    default="grok")


  options, args = parser.parse_args(sys.argv[1:])

  if not options.inputFile:
    parser.print_help()
    sys.exit(1)

  # Run it
  runAnomaly(options)



