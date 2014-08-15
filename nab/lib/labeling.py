#!/usr/bin/env python
import os
import yaml
import datetime
import dateutil.parser
import pandas

from nab.lib.corpus import Corpus
from nab.lib.util import absoluteFilePaths, flattenDict


class UserLabel(object):


  def __init__(self, path, dataRoot=None, corp=None):

    self.path = path
    self.dataRoot = dataRoot
    self.yaml = yaml.load(open(self.path,'r'))
    self.pathDict = flattenDict(yaml.load(open(self.path,'r')))
    if corp == None:
      self.corpus = Corpus(dataRoot)
    else:
      self.corpus = corp
    self.windows = self.getWindows()


  def getWindows(self):
    windows = {}

    def convertKey(key):
      return key + '.csv'

    for key in self.pathDict.keys():
      windows[convertKey(key)] = [[dateutil.parser.parse(t) for t in l]
                                                    for l in self.pathDict[key]]
    return windows


class LabelCombiner(object):

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
    ans = ''
    ans += 'labelRoot:           %s\n' % self.labelRoot
    ans += 'dataRoot:            %s\n' % self.dataRoot
    ans += 'corpus:              %s\n' % self.corpus
    ans += 'number of labels:    %d\n' % self.nlabelers
    ans += 'threshold:           %d\n' % self.threshold
    return ans


  def write(self, destDir):
    windows = yaml.dump(self.combinedWindows, default_flow_style=True)
    windowWriter = open(os.path.join(destDir, 'corpus_windows.yml'), 'w')
    windowWriter.writer(windows)

    labels = yaml.dump(self.combinedLabels, default_flow_style=True)
    labelWriter = open(os.path.join(destDir, 'corpus_labels.yml'), 'w')
    labelWriter.writer(labels)


  def combine(self):
    self.userLabels = self.getUserLabels()
    self.combineLabels()
    self.combineWindows()


  def getUserLabels(self):
    labelPaths = absoluteFilePaths(self.labelRoot)
    userLabels = [UserLabel(path, corp=self.corpus) for path in labelPaths]
    self.userLabels = userLabels
    self.nlabelers = len(self.userLabels)


  def combineLabels(self):
    labels = {}
    for relativePath, dataSet in self.corpus.dataSets.iteritems():
      timestampsHolder = []
      labelHolder = []

      for _, row in dataSet.data.iterrows():
        t = row['timestamp']

        count = 0

        for l in self.userLabels:
          if any(t >= t1 and t <= t2 for [t1,t2] in l.windows[relativePath]):
            count += 1

        label = int(count >= self.nlabelers*self.threshold)
        timestampsHolder.append(t)
        labelHolder.append(label)

      labels[relativePath] = pandas.DataFrame({'timestamp':timestampsHolder,
          'label': labelHolder})

    self.combinedLabels = labels


  def combineWindows(self):
    allWindows = {}

    def strf(t):
      return datetime.datetime.strftime(t, '%Y-%m-%d %H:%M:%S.%f')

    for relativePath, labels in self.combinedLabels.iteritems():
      delta = labels['timestamp'][1] - labels['timestamp'][0]

      labels = labels[labels['label'] == 1]
      dataSetWindows = []

      if labels.shape[0] == 0:
        dataSetWindows = []

      else:
        curr = None
        prev = None

        for _, row in labels.iterrows():
          curr = row['timestamp']
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
  def __init__(self, path, dataRoot, corpus=None):
    self.path = path
    self.dataRoot = dataRoot
    if not corpus:
      self.corpus = corpus.Corpus(dataRoot)
    else:
      self.corpus = corpus
    self.windows = None
    self.labels = None


  def getWindows(self):
    windowFile = open(os.path.join(self.path, 'corpus_windows.yml'), 'r')
    self.windows = yaml.load(windowFile)


  def getLabels(self):
    labelFile = open(os.path.join(self.path, 'corpus_labels.yml'), 'r')
    self.labels  = yaml.load(labelFile)
