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
import itertools
import pandas
import json

from nab.util import (absoluteFilePaths,
                      strf,
                      strp,
                      deepmap,
                      createPath)



class CorpusLabel(object):
  """Class to store and manipulate a single set of labels for the whole
  benchmark corpus."""

  def __init__(self, path, corpus):
    """
    @param path    (string)      Name of file containing the set of labels.

    @param corpus  (nab.Corpus)  Corpus object.
    """
    self.path = path

    self.windows = None
    self.labels = None

    self.corpus = corpus
    self.getWindows()
    self.getLabels()


  def getWindows(self):
    """
    Get windows as dictionaries with key value pairs of a relative path and its
    corresponding list of windows.
    """
    def found(t, data):
      f = data["timestamp"][data["timestamp"] == pandas.tslib.Timestamp(t)]

      exists = (len(f) == 1)

      if not exists:
        print t, "doesn't exist"

      return exists

    with open(os.path.join(self.path)) as windowFile:
      windows = json.load(windowFile)

    self.windows = {}

    for relativePath in windows.keys():

      self.windows[relativePath] = deepmap(strp, windows[relativePath])

      if len(self.windows[relativePath]) == 0:
        continue

      data = self.corpus.dataFiles[relativePath].data

      timestamps = list(itertools.chain(windows[relativePath]))[0]

      if not all(map((lambda t: found(t, data)), timestamps)):
        raise ValueError("timestamp listed in labels doesn't exist in file")


  def getLabels(self):
    """
    Get Labels as a dictionary of key value pairs of a relative path and its
    corresponding binary vector of anomaly labels. Labels are simple a more
    verbose version of the windows.
    """
    self.labels = {}

    for relativePath, dataSet in self.corpus.dataFiles.iteritems():
      windows = self.windows[relativePath]

      labels = pandas.DataFrame({"timestamp": dataSet.data["timestamp"]})
      labels['label'] = 0

      for t1, t2 in windows:
        moreThanT1 = labels[labels["timestamp"] >= t1]
        betweenT1AndT2 = moreThanT1[moreThanT1["timestamp"] <= t2]
        indices = betweenT1AndT2.loc[:,"label"].index
        labels["label"].values[indices] = 1

      self.labels[relativePath] = labels


class LabelCombiner(object):
  """
  This class is used to combine labels from multiple human labelers. The output
  is a single ground truth label file containing anomalies where there is
  enough human agreement. The class also computes the relaxed window around
  each anomaly.  The exact logic is described elsewhere in the NAB
  documentation.
  """

  def __init__(self, labelDir, corpus, threshold=1.0):
    """
    @param labelDir   (string)   A directory name containing user label files.
                                 This directory should contain one label file
                                 per human labeler.

    @param corpus     (Corpus)   Instance of Corpus class.

    @param threshold  (float)    A percentage between 0 and 1, specifying the
                                 agreement threshold.  It describes the level
                                 of agreement needed between individual
                                 labelers before a particular point in a
                                 data file is labeled as anomalous in the
                                 combined file.
    """
    self.labelDir = labelDir
    self.threshold = threshold
    self.corpus = corpus

    self.userLabels = None
    self.nlabelers = None

    self.combinedLabels = None
    self.combinedWindows = None


  def __str__(self):
    ans = ""
    ans += "labelDir:            %s\n" % self.labelDir
    ans += "corpus:              %s\n" % self.corpus
    ans += "number of labels:    %d\n" % self.nlabelers
    ans += "agreement threshold: %d\n" % self.threshold
    return ans


  def write(self, destPath):
    """Write the combined labels to a destination directory."""
    createPath(destPath)
    relaxedWindows = json.dumps(self.combinedRelaxedWindows, indent=3)
    with open(destPath, "w") as windowWriter:
      windowWriter.write(relaxedWindows)


  def combine(self):
    """Combine UserLabels."""
    self.getUserLabels()
    self.combineLabels()
    self.combineWindows()
    self.relaxWindows()


  def getUserLabels(self):
    """Collect UserLabels."""
    labelPaths = absoluteFilePaths(self.labelDir)

    self.userLabels = [CorpusLabel(path, self.corpus) for path in labelPaths]

    if len(self.userLabels) == 0:
      raise ValueError("No users labels found")

    self.nlabelers = len(self.userLabels)


  def combineLabels(self):
    """Combine windows to create raw labels.
    This uses the threshold to determine if a particular record should be
    labeled as 1 or 0. Threshold describes the level of agreement you want
    between labelers before you label a record as anomalous.
    """
    combinedLabels = {}

    for relativePath, dataSet in self.corpus.dataFiles.iteritems():
      timestamps = []
      labels = []

      for _, row in dataSet.data.iterrows():
        t = row["timestamp"]

        count = 0
        for user in self.userLabels:
          if any(t1 <= t <= t2 for [t1,t2] in user.windows[relativePath]):
            count += 1

        label = int(count >= self.nlabelers * self.threshold and count > 0)

        timestamps.append(t)
        labels.append(label)

      combinedLabels[relativePath] = pandas.DataFrame({"timestamp":timestamps,
        "label": labels})

    self.combinedLabels = combinedLabels


  def combineWindows(self):
    """Take raw combined labels and compress them to combinedWindows."""
    combinedWindows = {}

    for relativePath, labels in self.combinedLabels.iteritems():
      delta = labels["timestamp"][1] - labels["timestamp"][0]

      labels = labels[labels["label"] == 1]
      dataSetWindows = []

      if labels.shape[0] != 0:
        t1 = None
        t0 = None

        for _, row in labels.iterrows():
          t1 = row["timestamp"]

          if t0 is None:
            window = [strf(t1)]

          elif t1 - t0 != delta:
            window.append(strf(t0))
            dataSetWindows.append(window)
            window = [strf(t1)]

          t0 = t1

        window.append(strf(t1))
        dataSetWindows.append(window)

      combinedWindows[relativePath] = dataSetWindows

    self.combinedWindows = combinedWindows


  def relaxWindows(self, percentOfDataSet = 0.1):
    """
    This takes all windows and relaxes them (expands them) by a certain
    percentage of the data. A length (relaxWindowLength) is picked beforehand
    and each window is lengthened on both its left and right side by that
    length. This length is chosen as a certain percentage of the datafile.
    """
    allRelaxedWindows = {}

    for relativePath, limits in self.combinedWindows.iteritems():

      data = self.corpus.dataFiles[relativePath].data
      length = len(data["timestamp"])

      relaxWindowLength = int(percentOfDataSet*length)

      relaxedWindows = []

      # print "\n\n========================"
      # print "file=",relativePath, "relaxation amount=",relaxWindowLength

      for limit in limits:

        leftIndex = data[data["timestamp"] == limit[0]]["timestamp"].index[0]
        rightIndex = data[data["timestamp"] == limit[1]]["timestamp"].index[0]

        newLeftIndex = max(leftIndex - relaxWindowLength/2, 0)
        newRightIndex = min(rightIndex + relaxWindowLength/2, length-1)

        relaxedLimit = [strf(data["timestamp"][newLeftIndex]),
          strf(data["timestamp"][newRightIndex])]

        # print "original window indices=",leftIndex,rightIndex
        # print "relaxed indices=",newLeftIndex,newRightIndex
        # print "original timestamps=",limit
        # print "relaxed timestamps=",relaxedLimit

        relaxedWindows.append(relaxedLimit)

      allRelaxedWindows[relativePath] = relaxedWindows

    self.combinedRelaxedWindows = allRelaxedWindows
