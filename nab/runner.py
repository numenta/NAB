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
import pandas
import json
import multiprocessing


from nab.detectors.base import detectDataSet

from nab.corpus import Corpus
from nab.scorer import scoreCorpus
from nab.labeler import CorpusLabel
from nab.optimizer import optimizeThreshold

from nab.util import updateThresholds



class Runner(object):
  """Class to run a configured nab benchmark."""

  def __init__(self,
               dataDir,
               resultsDir,
               labelPath,
               profilesPath,
               thresholdPath,
               probationaryPercent=0.15,
               numCPUs=None):
    """
    @param dataDir        (string)  Directory where all the raw datasets exist.

    @param resultsDir     (string)  Directory where the detector anomaly scores
                                    will be scored.

    @param labelPath      (string)  Path where the labels of the datasets
                                    exist.

    @param profilesPath   (string)  Path to user profiles prescribing the
                                    username and the cost matrix.

    @param thresholdPath  (string)  Path to thresholds dictionary containing the
                                    best thresholds (and their corresponding
                                    score) for a combination of detector and
                                    user profile.

    @probationaryPercent  (float)   Percent of each dataset which will be
                                    ignored during the scoring process.

    @param numCPUs        (int)     Number of CPUs to be used for calls to
                                    multiprocessing.pool.map
    """
    self.dataDir = dataDir
    self.resultsDir = resultsDir

    self.labelPath = labelPath
    self.profilesPath = profilesPath
    self.thresholdPath = thresholdPath

    self.probationaryPercent = probationaryPercent
    self.pool = multiprocessing.Pool(numCPUs)

    self.corpus = None
    self.corpusLabel = None
    self.profiles = None


  def initialize(self):
    """Initialize all the relevant objects for the run."""
    self.corpus = Corpus(self.dataDir)
    self.corpusLabel = CorpusLabel(path=self.labelPath, corpus=self.corpus)

    with open(self.profilesPath) as p:
      self.profiles = json.load(p)


  def detect(self, detectors):
    """Generate results file given a dictionary of detector classes

    Function that takes a set of detectors and a corpus of data and creates a
    set of files storing the alerts and anomaly scores given by the detectors

    @param detectors     (dict)         Dictionary with key value pairs of a
                                        detector name and its corresponding
                                        class constructor.
    """
    print "\nObtaining Detections"

    count = 0
    args = []
    for detectorName, detectorConstructor in detectors.iteritems():
      for relativePath, dataSet in self.corpus.dataSets.iteritems():

        args.append(
          (
            count,
            detectorConstructor(
                          dataSet=dataSet,
                          probationaryPercent=self.probationaryPercent),
            detectorName,
            self.corpusLabel.labels[relativePath]["label"],
            self.resultsDir,
            relativePath
          )
        )

        count += 1

    print "calling multiprocessing pool"
    self.pool.map(detectDataSet, args)


  def optimize(self, detectorNames):
    """Optimize the threshold for each combination of detector and profile.

    @param detectorNames  (list)  List of detector names.

    @return thresholds    (dict)  Dictionary of dictionaries with detector names
                                  then usernames as keys followed by another
                                  dictionary containing the score and the
                                  threshold used to obtained that score.
    """
    print "\nOptimizing Anomaly Scores"

    thresholds = {}

    for detector in detectorNames:
      resultsDetectorDir = os.path.join(self.resultsDir, detector)
      resultsCorpus = Corpus(resultsDetectorDir)

      thresholds[detector] = {}

      for username, profile in self.profiles.iteritems():
        costMatrix = profile["CostMatrix"]

        thresholds[detector][username] = optimizeThreshold(
          (self.pool,
          detector,
          username,
          costMatrix,
          resultsCorpus,
          self.corpusLabel,
          self.probationaryPercent))

    updateThresholds(thresholds, self.thresholdPath)

    return thresholds


  def score(self, detectors, thresholds):
    """Score the performance of the detectors.

    Function that must be called only after detection result files have been
    generated and thresholds have been optimized. This looks at the result files
    and scores the performance of each detector specified and stores these
    results in a csv file.

    @param detectorNames  (list)    List of detector names.

    @param thresholds     (dict)    Dictionary of dictionaries with detector
                                    names then usernames as keys followed by
                                    another dictionary containing the score and
                                    the threshold used to obtained that score.
    """
    print "\nObtaining Benchmark Scores"

    for detector in detectors:
      ans = pandas.DataFrame(columns=("Detector", "Username", "File", \
        "Threshold", "Score", "tp", "tn", "fp", "fn", "Total_Count"))

      resultsDetectorDir = os.path.join(self.resultsDir, detector)
      resultsCorpus = Corpus(resultsDetectorDir)

      for username, profile in self.profiles.iteritems():

        costMatrix = profile["CostMatrix"]

        threshold = thresholds[detector][username]["threshold"]

        results = scoreCorpus(threshold,
                              (self.pool,
                               detector,
                               username,
                               costMatrix,
                               resultsCorpus,
                               self.corpusLabel,
                               self.probationaryPercent))

        for row in results:
          ans.loc[len(ans)] = row

      scorePath = os.path.join(resultsDetectorDir, detector + "_scores.csv")
      print "%s detector benchmark scores written to %s" %(detector, scorePath)
      ans.to_csv(scorePath, index=False)

