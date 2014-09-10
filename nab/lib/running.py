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
import math
import pandas
import yaml
import logging
import multiprocessing

from nab.lib.corpus import Corpus
from nab.lib.scoring import Scorer
from nab.lib.util import (detectorClassToName, convertResultsPathToDataPath)
from nab.lib.labeling import CorpusLabel

from collections import defaultdict



class Runner(object):
  """
  Class to run a configured nab benchmark
  """

  def __init__(self, rootDir, args, detectorClasses):
    """
    @param rootDir          (string)      Source directory of NAB or NAB-like
                                          directory with a data, label, results,
                                          and config directory.

    @param args             (namespace)   Class that holds many paramters of the
                                          run.

    @param detectorClasses  (list)        All the constructors for the detector
                                          classes to be used in this run.
    """
    self.rootDir = rootDir
    self.args = args

    self.dataDir = os.path.join(self.rootDir, self.args.dataDir)
    self.corp = Corpus(self.dataDir)

    self.labelDir = os.path.join(self.rootDir, self.args.labelDir)
    self.corpusLabel = self.getCorpusLabel()
    self.corpusLabel.getEverything()

    self.getDetectors(detectorClasses)
    self.resultsDir = \
    os.path.join(self.rootDir, args.resultsDir)
    self.probationaryPercent = args.probationaryPercent

    self.profiles = self.getProfiles()
    self.pool = multiprocessing.Pool(self.getNumCPUs())


  def detect(self):
    """
    Function that takes a set of detectors and a corpus of data and creates a
    set of files storing the alerts and anomaly scores given by the detectors
    """
    print "Obtaining detections"

    for detector, DetectorConstructor in self.detectors.iteritems():
      args = []


      for relativePath, dataSet in self.corp.dataSets.iteritems():

        args.append(DetectorConstructor(
          relativePath=relativePath,
          dataSet=dataSet,
          labels=self.corpusLabel.labels[relativePath],
          name=detector,
          probationaryPercent=self.probationaryPercent,
          outputDir=self.resultsDir))

    print "calling multiprocessing pool"

    self.pool.map(detectHelper, args)


  def score(self):
    """
    Function that must be called after detection result files have been
    generated. This looks at the result files and scores the performance of each
    detector specified and stores these results in a csv file.
    """
    print "Obtaining Scores"
    ans = pandas.DataFrame(columns=("Detector", "Username", "File",
      "Score", "tp", "tn", "fp", "fn", "Total_Count"))

    for detector in self.detectors.keys():
      resultsDetectorDir = os.path.join(self.resultsDir, detector)
      resultsCorpus = Corpus(resultsDetectorDir)

      args = []

      for username, profile in self.profiles.iteritems():

        costMatrix = profile["CostMatrix"]

        for relativePath, dataSet in resultsCorpus.dataSets.iteritems():


          relativePath = convertResultsPathToDataPath( \
            os.path.join(detector, relativePath))

          windows = self.corpusLabel.windows[relativePath]
          labels = self.corpusLabel.labels[relativePath]

          probationaryPeriod = math.floor(
            self.probationaryPercent * labels.shape[0])

          args.append(
            [detector,
             username,
             relativePath,
             dataSet,
             windows,
             labels,
             costMatrix,
             probationaryPeriod])

      print "calling multiprocessing pool"
      results = self.pool.map(scoreHelper, args)


      for i in range(len(results)):
        ans.loc[i] = results[i]

      scorePath = os.path.join(resultsDetectorDir, detector + "_scores.csv")
      ans.to_csv(scorePath, index=False)

  def getDetectors(self, constructors):
    """
    Creates a dictionary of detectors with detector names as keys and detector
    classes as values.

    @param constructors     (list)    All the constructors for the detector
                                      classes to be used in this run.

    @param                  (dict)    Dictionary with key value pairs of a
                                      detector name and its corresponding
                                      class constructor.
    """
    self.detectors = {}
    for c in constructors:
      self.detectors[detectorClassToName(c)] = c

    return self.detectors

  def getCorpusLabel(self):
    """
    Collects the corpus label.

    @return (CorpusLabel)   Label of the entire corpus.
    """
    return CorpusLabel(self.labelDir, None, self.corp)

  # def getConfig(self):
  #   f = open(os.path.join(self.rootDir, self.args.config))
  #   return yaml.load(f)

  def getProfiles(self):
    """
    Collects profiles specifying the confusion matrix parameters of each user.

    @return   (string)  The string version of the entire `user_profiles.yaml`
    """
    f = open(os.path.join(self.rootDir, self.args.profiles))
    return yaml.load(f)

  def getNumCPUs(self):
    """
    Returns the number of CPUs on the system unless prespecified.

    @return   (int)   Number of allowed CPUs that you can use to compute with.
                      If none is given, call multiprocessing.cpu_count()
    """
    if not self.args.numCPUs:
      return multiprocessing.cpu_count()
    return int(self.args.numCPUs)


def detectHelper(detectorInstance):
  """
  Function called in each detector process that run the detector that it is
  given.
  """
  d = detectorInstance
  print "Beginning detection with %s for %s" % (d.name, d.relativePath)
  detectorInstance.run()

def scoreHelper(args):
  """
  Function called to score each file in the corpus.
  """
  detector, username, relativePath, dataSet, windows, labels, \
  costMatrix, probationaryPeriod = args

  predicted = dataSet.data["alerts"]

  scorer = Scorer(
    predicted=predicted,
    labels=labels,
    windowLimits=windows,
    costMatrix=costMatrix,
    probationaryPeriod=probationaryPeriod)

  scorer.getScore()

  counts = scorer.counts

  return detector, username, relativePath, scorer.score, \
  counts["tp"], counts["tn"], counts["fp"], counts["fn"], \
  scorer.totalCount
