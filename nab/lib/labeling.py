#!/usr/bin/env python
import os
import yaml
import datetime
import dateutil.parser
import pandas
import pickle

import corpus
import util


class UserLabel(object):


  def __init__(self, path, dataRoot=None, corp=None):

    self.path = path
    self.dataRoot = dataRoot
    self.yaml = yaml.load(open(self.path,'r'))
    self.pathDict = flattenDict(yaml.load(open(self.path,'r')))
    if corp == None:
      self.corpus = corpus.Corpus(dataRoot)
    else:
      self.corpus = corp
    self.windows = self.getWindows()
    self.labels = self.getLabels()


  def getWindows(self):
    windows = {}

    def convertKey(key):
      return key + '.csv'

    for key in self.pathDict.keys():
      windows[convertKey(key)] = [[dateutil.parser.parse(t) for t in l]
                                                    for l in self.pathDict[key]]
    return windows


  def getLabels(self):
    labels = {}
    for key in self.windows.keys():
      l = []
      for [t1, t2] in self.windows[key]:
        l.extend(self.corpus.dataSets[key].getTimestampRange(t1, t2))
      labels[key] = l

    return labels


def flattenDict(dictionary, files={}, head=''):
  for key in dictionary.keys():
    concat = head + '/' + key if head != '' else key
    if type(dictionary[key]) is dict:
      flattenDict(dictionary[key], files, concat)
    else:
      files[concat] = dictionary[key]

  return files


class LabelCombiner(object):

  def __init__(self, labelRoot, dataRoot, destPath, threshold=1):
    self.labelRoot = labelRoot
    self.dataRoot = dataRoot
    self.destPath = destPath
    self.corpus = corpus.Corpus(dataRoot)
    self.userLabels = self.getUserLabels()
    self.nlabelers = len(self.userLabels)
    self.threshold = threshold
    self.combinedLabels = self.getCombinedLabels()
    self.combinedWindows = self.getCombinedWindows()
    self.write()

  def __str__(self):
    ans = ''
    ans += 'labelRoot:           %s\n' % self.labelRoot
    ans += 'dataRoot:            %s\n' % self.dataRoot
    ans += 'corpus:              %s\n' % self.corpus
    ans += 'number of labels:    %d\n' % self.nlabelers
    ans += 'threshold:           %d\n' % self.threshold
    return ans

  def write(self):
    pickle.dump(self.combinedWindows, open(os.path.join(self.destPath, 'corpus_windows.pkl'), 'w'))
    pickle.dump(self.combinedLabels, open(os.path.join(self.destPath, 'corpus_labels.pkl'), 'w'))


  def getUserLabels(self):
    labelPaths = util.absoluteFilePaths(self.labelRoot)
    userLabels = [UserLabel(path, corp=self.corpus) for path in labelPaths]
    return userLabels

  def getCombinedLabels(self):
    labels = {}
    for relativePath, dataSet in self.corpus.dataSets.iteritems():
      timestampsHolder = []
      labelHolder = []

      for i, row in dataSet.data.iterrows():
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

    return labels

  def getCombinedWindows(self):
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

        for i, row in labels.iterrows():
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


    return allWindows


class CorpusLabel(object):
  def __init__(self, path, dataRoot, corpus=None):
    self.path = path
    self.dataRoot = dataRoot
    if not corpus:
      self.corpus = corpus.Corpus(dataRoot)
    else:
      self.corpus = corpus

    self.windows = pickle.load(open(os.path.join(self.path, 'corpus_windows.pkl'), 'r'))
    self.labels  = pickle.load(open(os.path.join(self.path, 'corpus_labels.pkl'), 'r'))
