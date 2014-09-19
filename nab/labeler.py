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
import yaml
import dateutil.parser
import pandas
import json

from nab.corpus import Corpus
from nab.util import (absoluteFilePaths,
                      flattenDict,
                      strf,
                      strp,
                      deepmap,
                      makeDirsExist)



class UserLabel(object):
  """Class to store and manipulate a set of labels of a single labelers.

  Labels are stored as anomaly windows given by timestamps.
  """

  def __init__(self, path, dataRoot=None, corp=None):
    """
    @param path       (string)      Source path of yaml file containing the
                                    corpus labels for a single user.

    @param dataRoot   (string)      (optional) Source directory of corpus.

    @param corp       (nab.Corpus)  (optional) Corpus object.
    """
    if dataRoot is None and corp is None:
      raise ValueError()

    self.path = path
    self.dataRoot = dataRoot

    with open(self.path,"r") as f:
      self.yaml = yaml.load(f)

    self.pathDict = flattenDict(self.yaml)

    if corp == None:
      self.corpus = Corpus(dataRoot)
    else:
      self.corpus = corp
    self.windows = self.getWindows()


  def getWindows(self):
    """Store anomaly windows as dictionaries with the filename being the key."""
    windows = {}

    def convertKey(key):
      return key + ".csv"

    for key in self.pathDict.keys():
      data = self.corpus.dataSets[convertKey(key)].data

      for window in self.pathDict[key]:
        for t in window:
          t = t.decode('unicode_escape').encode('ascii','ignore')
          t = dateutil.parser.parse(t)
          found = data["timestamp"][data["timestamp"] == pandas.tslib.Timestamp(t)]
          if len(found) != 1:
            raise ValueError(
              "timestamp listed in labels don't exist in file")

      windows[convertKey(key)] = [[dateutil.parser.parse(t) for t in l]
                                                    for l in self.pathDict[key]]
    return windows


class CorpusLabel(object):
  """Class to store and manipulate the combined corpus labels."""

  def __init__(self, labelDir, dataDir=None, corp=None):
    """
    @param labelDir     (string)  Source directory of all label files created by
                                  users. (They should be in a format that is
                                  digestable by UserLabel)

    @param dataRoot   (string)      (optional) Source directory of corpus.

    @param corp       (nab.Corpus)  (optional) Corpus object.
    """
    self.labelDir = labelDir
    self.dataDir = dataDir

    if self.dataDir:
      self.corpus = Corpus(self.dataDir)
    else:
      self.corpus = corp

    self.rawWindows = None
    self.rawLabels = None
    self.windows = None
    self.labels = None


  def initialize(self):
    """Get boths labels and windows."""
    self.getWindows()
    self.getLabels()


  def getWindows(self):
    """
    Get windows as dictionaries with key value pairs of a relative path and its
    corresponding list of windows.
    """
    with open(os.path.join(self.labelDir, "corpus_windows.json")) as windowFile:
      windows = json.load(windowFile)

    self.rawWindows = windows
    self.windows = {}
    for relativePath in windows.keys():
      self.windows[relativePath] = deepmap(strp, windows[relativePath])


  def getLabels(self):
    """
    Get Labels as a dictionary of key value pairs of a relative path and its
    corresponding binary vector of anomaly labels. Labels are simple a more
    verbose version of the windows.
    """
    self.labels = {}

    for relativePath, dataSet in self.corpus.dataSets.iteritems():
      windows = self.windows[relativePath]

      labels = pandas.DataFrame({"timestamp": dataSet.data["timestamp"]})
      labels['label'] = 0

      for t1, t2 in windows:
        subset = labels[labels["timestamp"] >= t1][labels["timestamp"] <= t2]
        indices = subset.loc[:,"label"].index
        labels["label"].values[indices] = 1

      self.labels[relativePath] = labels


class LabelCombiner(object):
  """
  Class used to combine labels given many UserLabel objects. The process to
  combine labels is given in the NAB wiki.
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
    """Write the combined labels to a destination directory."""
    print self.combinedRelaxedWindows
    makeDirsExist(destDir)
    windows = json.dumps(self.combinedRelaxedWindows)
    with open(os.path.join(
      destDir, "corpus_windows.json"), "w") as windowWriter:
      windowWriter.write(windows)

    fileFriendlyLabels = {}

    for relativePath, label in self.combinedLabels.iteritems():
      fileFriendlyLabels[relativePath] = label
      fileFriendlyLabels[relativePath]["timestamp"] = \
                      fileFriendlyLabels[relativePath]["timestamp"].apply(strf)

      fileFriendlyLabels[relativePath] = \
        fileFriendlyLabels[relativePath].to_json()

    labels = json.dumps(fileFriendlyLabels)

    with open(os.path.join(destDir, "corpus_labels.json"), "w") as labelWriter:
      labelWriter.write(labels)


  def combine(self):
    """Combine UserLabels."""
    self.getUserLabels()
    self.combineLabels()
    self.combineWindows()
    self.relaxWindows()


  def getUserLabels(self):
    """Collect UserLabels."""
    labelPaths = absoluteFilePaths(self.labelRoot)
    userLabels = [UserLabel(path, corp=self.corpus) for path in labelPaths]
    self.userLabels = userLabels
    self.nlabelers = len(self.userLabels)


  def combineLabels(self):
    """Combine windows to create raw labels.
    This uses the threshold to determine if a particular record should be
    labeled as 1 or 0. Threshold describes the level of agreement you want
    between labelers before you label a record as anomalous.
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

        label = int(count >= self.nlabelers * self.threshold)
        timestampsHolder.append(t)
        labelHolder.append(label)

      labels[relativePath] = pandas.DataFrame({"timestamp":timestampsHolder,
          "label": labelHolder})

    self.combinedLabels = labels


  def combineWindows(self):
    """Take raw combined Labels and compress them to combinedWindows."""
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

  def relaxWindows(self):
    """
    This takes all windows and relaxes them by a certain percentage of the data.
    A length (relaxWindowLength) is picked before hand and each window is
    lengthened on both its left and right side by that length. This length is
    chosen as a certain percetange of the dataset.
    """
    allRelaxedWindows = {}
    for relativePath, limits in self.combinedWindows.iteritems():
      data = self.corpus.dataSets[relativePath].data
      length = len(data["timestamp"])
      percentOfDataSet = 0.025
      numWindows = len(limits)
      relaxWindowLength = int(percentOfDataSet*length)

      relaxedWindows = []
      for i, limit in enumerate(limits):
        t1, t2 = limit
        indices = map((
          lambda t: data["timestamp"][data["timestamp"] == t].index[0]),
          limit)
        t1Index = max(indices[0] - relaxWindowLength, 0)
        t2Index = min(indices[0] + relaxWindowLength, length-1)
        relaxedLimit = [strf(data["timestamp"][t1Index]),
          strf(data["timestamp"][t2Index])]

        relaxedWindows.append(relaxedLimit)
      allRelaxedWindows[relativePath] = relaxedWindows

    self.combinedRelaxedWindows = allRelaxedWindows
