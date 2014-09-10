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
                          createPath)
from nab.lib.labeling import CorpusLabel



class Runner(object):
  """Class to run a configured nab benchmark."""

  def __init__(self, args):
    """
    @param rootDir          (string)      Source directory of NAB or NAB-like
                                          directory with a data, label, results,
                                          and config directory.

    @param args             (namespace)   Class that holds many paramters of the
                                          run.

    @param detectorClasses  (list)        All the constructors for the detector
                                          classes to be used in this run.
    """
    self.args = args

    self.probationaryPercent = args.probationaryPercent

    self.pool = multiprocessing.Pool(args.numCPUs)

    self.corpus = None
    self.corpusLabel = None
    self.profiles = None


  def initialize(self):

    print "Creating corpus"
    self.corpus = Corpus(self.args.dataDir)

    print "Creating corpus label"
    self.corpusLabel = CorpusLabel(self.args.labelDir, None, self.corpus)

    print "Initializing corpus label"
    self.corpusLabel.initialize()

    print "Getting profiles"
    self.profiles = yaml.load(open(self.args.profilePath))


  def detect(self, detectorClasses):
    """
    Function that takes a set of detectors and a corpus of data and creates a
    set of files storing the alerts and anomaly scores given by the detectors

    @param detectorClasses
    """
    print "\nObtaining detections"

    detectors = createDetectorDictionary(detectorClasses)
    count = 0
    for detectorName, detectorConstructor in detectors.iteritems():
      args = []

      for relativePath, dataSet in self.corpus.dataSets.iteritems():

        args.append(
          (
            count,
            detectorConstructor(
                          dataSet=dataSet,
                          probationaryPercent=self.probationaryPercent),
            detectorName,
            self.corpusLabel.labels[relativePath]["label"],
            self.args.resultsDir,
            relativePath
          )
        )

        count += 1

    print "calling multiprocessing pool"
    self.pool.map(detectHelper, args)


  def score(self, detectorNames):
    """
    Function that must be called after detection result files have been
    generated. This looks at the result files and scores the performance of each
    detector specified and stores these results in a csv file.
    """
    print "\nObtaining Scores"
    ans = pandas.DataFrame(columns=("Detector", "Username", "File",
      "Score", "tp", "tn", "fp", "fn", "Total_Count"))

    for detector in detectorNames:
      resultsDetectorDir = os.path.join(self.args.resultsDir, detector)
      resultsCorpus = Corpus(resultsDetectorDir)

      args = []

      for username, profile in self.profiles.iteritems():

        costMatrix = profile["CostMatrix"]

        print resultsCorpus.dataSets

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
             dataSet.data["alerts"],
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


def createDetectorDictionary(constructors):
  """
  Creates a dictionary of detectors with detector names as keys and detector
  classes as values.

  @param constructors     (list)    All the constructors for the detector
                                    classes to be used in this run.

  @param                  (dict)    Dictionary with key value pairs of a
                                    detector name and its corresponding
                                    class constructor.
  """
  detectors = {}
  for c in constructors:
    detectors[detectorClassToName(c)] = c

  return detectors


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


def scoreHelper(args):
  """
  Function called to score each file in the corpus.
  """
  (detectorName,
   username,
   relativePath,
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

  return detectorName, username, relativePath, scorer.score, \
  counts["tp"], counts["tn"], counts["fp"], counts["fn"], \
  scorer.totalCount
