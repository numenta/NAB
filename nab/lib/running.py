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
import multiprocessing

from datetime import datetime

from nab.lib.corpus import Corpus
from nab.lib.scoring import Scorer
from nab.lib.util import (detectorClassToName,
                          convertResultsPathToDataPath,
                          createPath,
                          convertAnomalyScoresToDetections)
from nab.lib.labeling import CorpusLabel



class Runner(object):
  """Class to run a configured nab benchmark."""

  def __init__(self, args):
    """
    @param args             (namespace)   Class that holds many paramters of the
                                          run.
    """
    self.args = args

    self.pool = multiprocessing.Pool(args.numCPUs)

    self.corpus = None
    self.corpusLabel = None
    self.profiles = None


  def initialize(self):
    """Initialize all the relevant objects for the run."""

    self.corpus = Corpus(self.args.dataDir)
    self.corpusLabel = CorpusLabel(self.args.labelDir, None, self.corpus)
    self.corpusLabel.initialize()

    with open(self.args.profilesPath) as p:
      self.profiles = yaml.load(p)


  def detect(self, detectors):
    """Generate results file given a dictionary of detector classes

    Function that takes a set of detectors and a corpus of data and creates a
    set of files storing the alerts and anomaly scores given by the detectors

    @param detectors     (dict)         Dictionary with key value pairs of a
                                        detector name and its corresponding
                                        class constructor.
    """
    print "\nObtaining detections"

    count = 0
    for detectorName, detectorConstructor in detectors.iteritems():
      args = []

      for relativePath, dataSet in self.corpus.dataSets.iteritems():

        args.append(
          (
            count,
            detectorConstructor(
                          dataSet=dataSet,
                          probationaryPercent=self.args.probationaryPercent),
            detectorName,
            self.corpusLabel.labels[relativePath]["label"],
            self.args.resultsDir,
            relativePath
          )
        )

        count += 1

    print "calling multiprocessing pool"
    self.pool.map(detectHelper, args)


  def optimize_threshold(self, detectorNames):
    """Optimize the threshold for each combination of detector and profile.

    @param detectorNames  (list)  List of detector names.

    @return thresholds     (dict) Dictionary of dictionaries with detector names
                                  then usernames as keys followed by another
                                  dictionary containing the score and the
                                  threshold used to obtained that score.
    """
    print "\nOptimizing anomaly Scores"

    thresholds = dict()

    for detector in detectorNames:
      resultsDetectorDir = os.path.join(self.args.resultsDir, detector)
      resultsCorpus = Corpus(resultsDetectorDir)

      thresholds[detector] = dict()

      for username, profile in self.profiles.iteritems():
        costMatrix = profile["CostMatrix"]

        thresholds[detector][username] = optimize(
          (self.pool,
          detector,
          username,
          costMatrix,
          resultsCorpus,
          self.corpusLabel,
          self.args.probationaryPercent))

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
    print "\nObtaining Scores"

    ans = pandas.DataFrame(columns=("Detector", "Username", "File",
      "Threshold", "Score", "tp", "tn", "fp", "fn", "Total_Count"))

    for detector in detectors:
      resultsDetectorDir = os.path.join(self.args.resultsDir, detector)
      resultsCorpus = Corpus(resultsDetectorDir)

      args = []

      for username, profile in self.profiles.iteritems():

        costMatrix = profile["CostMatrix"]

        threshold = thresholds[detector][username]["threshold"]

        for relativePath, dataSet in resultsCorpus.dataSets.iteritems():

          relativePath = convertResultsPathToDataPath( \
            os.path.join(detector, relativePath))

          windows = self.corpusLabel.windows[relativePath]
          labels = self.corpusLabel.labels[relativePath]

          probationaryPeriod = math.floor(
            self.args.probationaryPercent * labels.shape[0])

          predicted = convertAnomalyScoresToDetections(
            dataSet.data["anomaly_score"], threshold)

          args.append(
            [detector,
             username,
             relativePath,
             threshold,
             predicted,
             windows,
             labels,
             costMatrix,
             probationaryPeriod])

    print "calling multiprocessing pool"
    results = self.pool.map(scoreHelper, args)

    for i in range(len(results)):
      ans.loc[i] = results[i]

    scorePath = os.path.join(resultsDetectorDir, "scores.csv")
    ans.to_csv(scorePath, index=False)



def detectHelper(args):
  """
  Function called in each detector process that run the detector that it is
  given.
  """
  (i, detectorInstance, detectorName, labels, outputDir, relativePath) = args

  relativeDir, fileName = os.path.split(relativePath)
  fileName =  detectorName + "_" + fileName
  outputPath = os.path.join(outputDir, detectorName, relativeDir, fileName)
  createPath(outputPath)

  print "%s: Beginning detection with %s for %s" % \
                                                (i, detectorName, relativePath)

  results = detectorInstance.run()

  results["label"] = labels

  results.to_csv(outputPath, index=False, float_format="%.3f")

  print "%s: Completed processing %s records  at %s" % \
                                        (i, len(results.index), datetime.now())
  print "%s: Results have been written to %s" % (i, outputPath)


def optimize(args, tolerance=0.00001):
  threshold = 0.5
  step = 0.1
  bestScore = fitnessFunction(threshold, args)

  while step > tolerance:
    threshold += step
    score = fitnessFunction(threshold, args)

    if score > bestScore:
      bestScore = score
      step *= 2

    else:
      threshold -= 2*step
      score = fitnessFunction(threshold, args)

      if score > bestScore:
        bestScore = score
        step *= 2
      else:
        threshold += step
        step *= 0.5

    print "threshold:", threshold
    print "bestScore:", bestScore
    print "step:", step
    print

  return {"threshold": threshold,
          "score": bestScore}


def fitnessFunction(threshold, args):
  if not 0 <= threshold <= 1:
    return float("-inf")

  score = 0
  (pool,
   detector,
   username,
   costMatrix,
   resultsCorpus,
   corpusLabel,
   probationaryPercent) = args

  args = []
  for relativePath, dataSet in resultsCorpus.dataSets.iteritems():

    relativePath = convertResultsPathToDataPath( \
      os.path.join(detector, relativePath))

    windows = corpusLabel.windows[relativePath]
    labels = corpusLabel.labels[relativePath]

    probationaryPeriod = math.floor(
      probationaryPercent * labels.shape[0])

    predicted = convertAnomalyScoresToDetections(
      dataSet.data["anomaly_score"], threshold)

    args.append((
      detector,
      username,
      relativePath,
      threshold,
      predicted,
      windows,
      labels,
      costMatrix,
      probationaryPeriod))

  results = pool.map(scoreHelper, args)
  score = 0

  for r in results:
    score += r[4]

  return score


def scoreHelper(args):
  """
  Function called to score each file in the corpus.
  """
  (detectorName,
   username,
   relativePath,
   threshold,
   predicted,
   windows,
   labels,
   costMatrix,
   probationaryPeriod) = args

  scorer = Scorer(
    predicted=predicted,
    labels=labels,
    windowLimits=windows,
    costMatrix=costMatrix,
    probationaryPeriod=probationaryPeriod)

  scorer.getScore()

  counts = scorer.counts

  return detectorName, username, relativePath, threshold, scorer.score, \
  counts["tp"], counts["tn"], counts["fp"], counts["fn"], \
  scorer.totalCount
