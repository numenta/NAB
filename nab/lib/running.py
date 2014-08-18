import os
import math
import pandas
import yaml
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
    self.numCPUs = self.getNumCPUs()
    self.plot = options.plotResults


  def detect(self):
    print "Obtaining detections"
    print self.detectors
    for detectorName, detectorConstructor in self.detectors.iteritems():
      print detectorName
      instance = detectorConstructor(
        corpus=self.corp,
        labels=self.corpusLabel,
        name=detectorName,
        probationaryPercent=self.probationaryPercent,
        outputDir=self.resultsDir,
        numCPUs=self.numCPUs)

      instance.runCorpus()

  def score(self):
    print "Obtaining Scores"

    for detectorName in self.detectors.keys():
      ans = defaultdict(list)
      resultsDetectorDir = os.path.join(self.resultsDir, detectorName)
      resultsCorpus = Corpus(resultsDetectorDir)

      dataSets = resultsCorpus.getDataSubset('/alerts/')

      for profileName, profile in self.profiles.iteritems():

        costMatrix = profile['CostMatrix']

        for relativePath in dataSets.keys():

          predicted = dataSets[relativePath].data['alert']
          relativePath = convertResultsPathToDataPath(os.path.join(detectorName, relativePath))

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

          ans["Detector"].append(detectorName)
          ans["Username"].append(profileName)
          ans["File"].append(relativePath)
          ans["Score"].append(scorer.score)
          ans["tp"].append(counts['tp'])
          ans["tn"].append(counts['tn'])
          ans["fp"].append(counts['fp'])
          ans["fn"].append(counts['fn'])
          ans["Total Count"].append(scorer.totalCount)

      ans = pandas.DataFrame(ans)

      scorePath = os.path.join(resultsDetectorDir, detectorName+"_scores.csv")
      ans.to_csv(scorePath, index=False)

  def getDetectors(self, constructors):
    self.detectors = {}
    for c in constructors:
      print 'in getDetectors'
      print c
      print detectorClassToName(c)
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
