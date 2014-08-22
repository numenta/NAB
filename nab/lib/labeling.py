#!/usr/bin/env python
import os
import yaml
import dateutil.parser
import pandas
import json

from nab.lib.corpus import Corpus
from nab.lib.util import absoluteFilePaths, flattenDict, strf, strp, deepmap

class UserLabel(object):
  """
  Class to store and manipulate a set of labels of a single labelers. Labels
  are stored as anomaly windows given by timestamps.
  """

  def __init__(self, path, dataRoot=None, corp=None):

    self.path = path
    self.dataRoot = dataRoot
    self.yaml = yaml.load(open(self.path,"r"))

    self.pathDict = flattenDict(yaml.load(open(self.path,"r")))

    if corp == None:
      self.corpus = Corpus(dataRoot)
    else:
      self.corpus = corp
    self.windows = self.getWindows()


  def getWindows(self):
    """
    Anomaly windows are stored as dictionary with the filename being the key
    """
    windows = {}

    def convertKey(key):
      return key + ".csv"

    for key in self.pathDict.keys():

      windows[convertKey(key)] = [[dateutil.parser.parse(t) for t in l]
                                                    for l in self.pathDict[key]]
    return windows


class LabelCombiner(object):
  """
  Class used to combine labels given many UserLabel objects. The process to
  combine labels is given in the NAB wiki
  """

  def __init__(self, labelRoot, dataRoot, threshold=1):
    self.labelRoot = labelRoot
    self.dataRoot = dataRoot
    self.threshold = threshold
    self.corpus = Corpus(dataRoot)

    self.userLabels = None
    self.nlabelers = None

    self.combinedLabels = None
    self.combinedWindows = None


  def __str__(self):
    ans = ""
    ans += "labelRoot:           %s\n" % self.labelRoot
    ans += "dataRoot:            %s\n" % self.dataRoot
    ans += "corpus:              %s\n" % self.corpus
    ans += "number of labels:    %d\n" % self.nlabelers
    ans += "threshold:           %d\n" % self.threshold
    return ans


  def write(self, destDir):
    """
    Write the combined labels to a destination directory
    """

    windows = json.dumps(self.combinedWindows)
    windowWriter = open(os.path.join(destDir, "corpus_windows.json"), "w")
    windowWriter.write(windows)

    fileFriendlyLabels = {}

    for relativePath, label in self.combinedLabels.iteritems():
      fileFriendlyLabels[relativePath] = label
      fileFriendlyLabels[relativePath]["timestamp"] = \
                      fileFriendlyLabels[relativePath]["timestamp"].apply(strf)

      fileFriendlyLabels[relativePath] = fileFriendlyLabels[relativePath].to_json()

    labels = json.dumps(fileFriendlyLabels)
    labelWriter = open(os.path.join(destDir, "corpus_labels.json"), "w")
    labelWriter.write(labels)


  def combine(self):
    """
    Combine UserLabel's
    """
    self.getUserLabels()
    self.combineLabels()
    self.combineWindows()


  def getUserLabels(self):
    """
    Collect UserLabels
    """
    labelPaths = absoluteFilePaths(self.labelRoot)
    userLabels = [UserLabel(path, corp=self.corpus) for path in labelPaths]
    self.userLabels = userLabels
    self.nlabelers = len(self.userLabels)


  def combineLabels(self):
    """
    Combine windows to create raw labels
    """
    labels = {}
    for relativePath, dataSet in self.corpus.dataSets.iteritems():
      timestampsHolder = []
      labelHolder = []

      for _, row in dataSet.data.iterrows():
        t = row["timestamp"]

        count = 0
        for l in self.userLabels:
          if any(t >= t1 and t <= t2 for [t1,t2] in l.windows[relativePath]):
            count += 1

        label = int(count >= self.nlabelers*self.threshold)
        timestampsHolder.append(t)
        labelHolder.append(label)

      labels[relativePath] = pandas.DataFrame({"timestamp":timestampsHolder,
          "label": labelHolder})

      # labels[relativePath] = labels[relativePath].to_dict()

    self.combinedLabels = labels


  def combineWindows(self):
    """
    Take raw combined Labels and compress them to combinedWindows
    """
    allWindows = {}

    for relativePath, labels in self.combinedLabels.iteritems():
      delta = labels["timestamp"][1] - labels["timestamp"][0]

      labels = labels[labels["label"] == 1]
      dataSetWindows = []

      if labels.shape[0] == 0:
        dataSetWindows = []

      else:
        curr = None
        prev = None

        for _, row in labels.iterrows():
          curr = row["timestamp"]
          if not prev:
            currentWindow = [strf(curr)]

          elif curr - prev != delta:
            currentWindow.append(strf(prev))
            dataSetWindows.append(currentWindow)
            currentWindow = [strf(curr)]

          prev = curr

        currentWindow.append(strf(curr))
        dataSetWindows.append(currentWindow)

      allWindows[relativePath] = dataSetWindows


    self.combinedWindows = allWindows


class CorpusLabel(object):
  """
  Class to store and manipulate the combined corpus label.
  """
  def __init__(self, labelDir, dataDir=None, corpus=None):
    self.labelDir = labelDir
    self.dataDir = dataDir

    if self.dataDir:
      self.corpus = Corpus(self.dataDir)
    else:
      self.corpus = corpus

    self.rawWindows = None
    self.rawLabels = None
    self.windows = None
    self.labels = None

  def getEverything(self):
    """
    Get boths labels and windows.
    """
    self.getWindows()
    self.getLabels()

  def getWindows(self):
    """
    Get windows.
    """
    windowFile = open(os.path.join(self.labelDir, "corpus_windows.json"), "r")
    windows = json.load(windowFile)
    self.rawWindows = windows
    self.windows = {}
    for relativePath in windows.keys():
      self.windows[relativePath] = deepmap(strp, windows[relativePath])

  def getLabels(self):
    """
    Get Labels.
    """
    labelFile = open(os.path.join(self.labelDir, "corpus_labels.json"), "r")
    labels  = json.load(labelFile)
    self.rawLabels = labels
    self.labels = {}

    for relativePath, value in labels.iteritems():
      value = pandas.io.json.read_json(value)
      value["timestamp"] = value["timestamp"].apply(strp)
      self.labels[relativePath] = value
