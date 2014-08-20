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

  def __init__(self, rootDir, options, detectorClasses):
    self.rootDir = rootDir
    self.options = options

    self.dataDir = os.path.join(self.rootDir, self.options.dataDir)
    self.corp = Corpus(self.dataDir)

    self.labelDir = os.path.join(self.rootDir, self.options.labelDir)
    self.corpusLabel = self.getCorpusLabel()
    self.corpusLabel.getEverything()

    self.config = self.getConfig()
    self.getDetectors(detectorClasses)
    self.resultsDir = \
    os.path.join(self.rootDir, self.config["ResultsDirectory"])
    self.probationaryPercent = self.config["ProbationaryPercent"]

    self.profiles = self.getProfiles()
    # self.pool = multiprocessing.Pool(self.getNumCPUs())
    self.pool = multiprocessing.Pool(1)


  def detect(self):
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
    self.detectors = {}
    for c in constructors:
      self.detectors[detectorClassToName(c)] = c

    return self.detectors

  def getCorpusLabel(self):
    return CorpusLabel(self.labelDir, None, self.corp)

  def getConfig(self):
    f = open(os.path.join(self.rootDir, self.options.config))
    return yaml.load(f)

  def getProfiles(self):
    f = open(os.path.join(self.rootDir, self.options.profiles))
    return yaml.load(f)

  def getNumCPUs(self):
    if not self.options.numCPUs:
      return multiprocessing.cpu_count()
    return int(self.options.numCPUs)


def detectHelper(detectorInstance):
  d = detectorInstance
  print "Beginning detection with %s for %s" % (d.name, d.relativePath)
  detectorInstance.run()

def scoreHelper(args):

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
