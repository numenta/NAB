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
import yaml
import copy

from optparse import OptionParser
from multiprocessing import Pool, cpu_count

from lib
from run_anomaly import runAnomaly
from analyze_results import analyzeResults

from detectors import (NumentaDetector, SkylineDetector)

class Runner(object):

  def __init__(self, options):
    self.options = options
    self.root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    self.config = self.getConfig()
    self.detectors = self.config["AnomalyDetectors"]
    self.dataGroups = self.config["DataGroups"]
    self.resultsDir = os.path.join(self.root, self.config["ResultsDirectory"])
    self.labels = self.getLabels()
    self.profiles = self.getProfiles()
    self.numCPUs = self.getNumCPUs()
    self.plot = options.plotResults
    self.results = self.getResults()
    self.analysis = self.getAnalysis()


  def getResults(self):
    pool = Pool(processes=self.numCPUs)

    tasks = []
    for detector in self.detectors:

      for dataGroup in self.DataGroups:

        dataPath = os.path.join(self.root, "data", dataGroup)
        groupCorpus = lib.corpus.Corpus(dataPath)




        # fileNames = util.absoluteFilePaths(dataPath)

        # for fileName in fileNames:
        #   subOpt = copy.deepcopy(options)

        #   subOpt.detector = detector
        #   subOpt.dataGroup = dataGroup
        #   subOpt.inputFile = fileName
        #   subOpt.outputFile = None

        #   # Add in options used when running run_anomaly.py stand-alone
        #   subOpt.min = None
        #   subOpt.max = None

        #   subOpt.outputDir = os.path.join(self.resultsDir, detector)
        #   tasks.append(subOpt)

    print "Running %d tasks using %d cores ..." % (len(tasks), self.numCPUs)

    pool.map(runAnomaly, tasks)

  def getAnalysis(self):
    tasks = []
    for detector in self.detectors:
      subOpt = copy.deepcopy(options)
      subOpt.plot = self.plot
      resultsDetectorDir = os.path.join(self.resultsDir, detector)
      subOpt.resultsDir = resultsDetectorDir
      # Plotting in parallel fails, so don't use pool
      if self.plot:
        analyzeResults(subOpt)
      else:
        tasks.append(subOpt)

    if tasks:
      pool = Pool(processes=self.numCPUs)
      pool.map(analyzeResults, tasks)

  def getLabels(self):
    return label(options.labelsDir)

  def getConfig(self):
    f = open(os.path.join(self.root, options.config))
    return yaml.load(f)

  def getProfiles(self):
    f = open(os.path.join(self.root, options.profiles))
    return yaml.load(f)

  def getNumCPUs(self):
    if not self.options.numCPUs:
      return cpu_count()
    return int(self.options.numCPUs)


  def runAnomaly(self, corpus, outputDir):
    """
    Run selected detector on selected file
    """
    outputDir = getOutputDir(options)

    detectorClass = getDetectorClass(self, detector)

    detectorClass.runCorpus()


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

def getDetectorHandle(detector):
  # If the detector is 'detector', the detector class must be named
    # DetectorDetector# If the detector is 'detector', the detector class must be named
  detector = detector[0].upper() + detector[1:]

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
  return detectorClass


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


if __name__ == "__main__":

  parser = OptionParser()
  parser.add_option("-a", "--analyzeOnly",
                    help="Analyze results in the results directory only.",
                    dest="analyzeOnly",
                    default=False,
                    action="store_true")

  parser.add_option("-r", "--resultsOnly",
                    help="Generate detector results but do not analyze results \
                    files.",
                    dest="resultsOnly",
                    default=False,
                    action="store_true")

  parser.add_option("-p", "--plot",
                    help="If you have Plotly installed "
                    "this option will plot results and ROC curves for each \
                    dataset.",
                    dest="plotResults",
                    default=False,
                    action="store_true")

  parser.add_option("--verbosity",
                    default=0,
                    help="Increase the amount and detail of output by setting \
                    this greater than 0.")

  parser.add_option("--config",
                    default="scripts/config/benchmark_config.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_option(
                    "--profiles",
                    default="scripts/config/user_profiles.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_option("--numCPUs",
                    help="The number of CPUs to use to run the "
                    "benchmark. If not specified all CPUs will be used.")

  parser.add_option("--labelDir",
                    default="labels",
                    help="This holds all the label windows for the corpus.")

  options, args = parser.parse_args()

  Runner(options)
