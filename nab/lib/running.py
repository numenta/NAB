import os
import math
import pandas
import yaml
import multiprocessing

from nab.lib.corpus import Corpus
from nab.lib.scoring import Scorer
from nab.lib.util import (getDetectorClassName, convertResultsPathToDataPath)
from nab.lib.labeling import CorpusLabel

from nab.detectors.numenta.numenta_detector import NumentaDetector
from nab.detectors.skyline.skyline_detector import SkylineDetector

from collections import defaultdict

class Runner(object):

  def __init__(self, root, options):
    self.root = root
    self.options = options

    self.dataDir = os.path.join(self.root, self.options.dataDir)
    self.corp = Corpus(self.dataDir)

    self.labelDir = os.path.join(self.root, self.options.labelDir)
    self.corpusLabel = self.getCorpusLabel()

    self.config = self.getConfig()
    self.detectors = self.config["AnomalyDetectors"]
    self.resultsDir = os.path.join(self.root, self.config["ResultsDirectory"])
    self.probationaryPercent = self.config["ProbationaryPercent"]

    self.profiles = self.getProfiles()
    self.numCPUs = self.getNumCPUs()
    self.plot = options.plotResults

  def getAlerts(self):
    print "Obtaining Alerts"
    for detector in self.detectors:
      print detector
      detectorClassName = getDetectorClassName(detector)

      detectorClass = globals()[detectorClassName](
        corpus=self.corp,
        labels=self.corpusLabel,
        name=detector,
        probationaryPercent=self.probationaryPercent,
        outputDir=self.resultsDir,
        numCPUs=self.numCPUs)

      detectorClass.runCorpus()


  def getScores(self):
    print "Obtaining Scores"
    analysis = defaultdict(list)
    for detector in self.detectors:

      resultsDetectorDir = os.path.join(self.resultsDir, detector)
      resultsCorpus = Corpus(resultsDetectorDir)

      dataSets = resultsCorpus.getDataSubset('/alerts/')

      for profileName, profile in self.profiles.iteritems():

        costMatrix = profile['CostMatrix']

        for relativePath in dataSets.keys():

          predicted = dataSets[relativePath].data['alert']

          relativePath = convertResultsPathToDataPath(os.path.join(detector, relativePath))
          windows = self.corpusLabel.windows[relativePath]
          labels = self.corpusLabel.labels[relativePath]

          probationaryPeriod = math.floor(self.probationaryPercent*labels.shape[0])

          scorer = Scorer(
            predicted=predicted,
            labels=labels,
            windowLimits=windows,
            costMatrix=costMatrix,
            probationaryPeriod=probationaryPeriod)

          scorer.getScore()

          analysis["Detector"].append(detector)
          analysis["Username"].append(profileName)
          analysis["File"].append(relativePath)
          analysis["Score"].append(scorer.score)

      analysis = pandas.DataFrame(analysis)

    analysisPath = os.path.join(resultsDetectorDir, "analysis.csv")
    analysis.to_csv(analysisPath)

  def getCorpusLabel(self):
    return CorpusLabel(self.labelDir, None, self.corp)

  def getConfig(self):
    f = open(os.path.join(self.root, self.options.config))
    return yaml.load(f)

  def getProfiles(self):
    f = open(os.path.join(self.root, self.options.profiles))
    return yaml.load(f)

  def getNumCPUs(self):
    if not self.options.numCPUs:
      return multiprocessing.cpu_count()
    return int(self.options.numCPUs)
