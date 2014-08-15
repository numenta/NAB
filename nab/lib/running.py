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
    self.corpusLabel.getEverything()

    self.config = self.getConfig()
    self.detectors = self.config["AnomalyDetectors"]
    self.resultsDir = os.path.join(self.root, self.config["ResultsDirectory"])
    self.probationaryPercent = self.config["ProbationaryPercent"]

    self.profiles = self.getProfiles()
    self.numCPUs = self.getNumCPUs()
    self.plot = options.plotResults

  def detect(self):
    print "Obtaining detections"
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

  def score(self):
    print "Obtaining Scores"

    for detector in self.detectors:
      ans = defaultdict(list)
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

          counts = scorer.counts

          ans["Detector"].append(detector)
          ans["Username"].append(profileName)
          ans["File"].append(relativePath)
          ans["Score"].append(scorer.score)
          ans["tp"].append(counts['tp'])
          ans["tn"].append(counts['tn'])
          ans["fp"].append(counts['fp'])
          ans["fn"].append(counts['fn'])
          ans["Total Count"].append(scorer.totalCount)

      ans = pandas.DataFrame(ans)

      scorePath = os.path.join(resultsDetectorDir, detector+"_scores.csv")
      ans.to_csv(scorePath)

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
