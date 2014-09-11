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
import sys
import yaml
import dateutil.parser
import pandas
import json

from nab.lib.corpus import Corpus
from nab.lib.util import (absoluteFilePaths,
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
    print "Getting windows"
    self.getWindows()
    print "Getting Labels"
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
    with open(os.path.join(self.labelDir, "corpus_labels.json"), "r") as lFile:
      labels = json.load(lFile)
    self.rawLabels = labels
    self.labels = {}

    for relativePath, value in labels.iteritems():
      value = pandas.io.json.read_json(value)
      value["timestamp"] = value["timestamp"].apply(strp)
      self.labels[relativePath] = value


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
    makeDirsExist(destDir)
    windows = json.dumps(self.combinedWindows)
    with open(os.path.join(destDir, "corpus_windows.json"), "w") as windowWriter:
      windowWriter.write(windows)

    fileFriendlyLabels = {}

    for relativePath, label in self.combinedLabels.iteritems():
      fileFriendlyLabels[relativePath] = label
      fileFriendlyLabels[relativePath]["timestamp"] = \
                      fileFriendlyLabels[relativePath]["timestamp"].apply(strf)

      fileFriendlyLabels[relativePath] = fileFriendlyLabels[relativePath].to_json()

    labels = json.dumps(fileFriendlyLabels)

    with open(os.path.join(destDir, "corpus_labels.json"), "w") as labelWriter:
      labelWriter.write(labels)


  def combine(self):
    """Combine UserLabels."""
    self.getUserLabels()
    self.combineLabels()
    self.combineWindows()


  def getUserLabels(self):
    """Collect UserLabels."""
    labelPaths = absoluteFilePaths(self.labelRoot)
    userLabels = [UserLabel(path, corp=self.corpus) for path in labelPaths]
    self.userLabels = userLabels
    self.nlabelers = len(self.userLabels)


  def combineLabels(self):
    """Combine windows to create raw labels."""
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
