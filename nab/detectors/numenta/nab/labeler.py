# ----------------------------------------------------------------------
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import datetime
import itertools
import numpy
import os
import pandas
try:
  import simplejson as json
except ImportError:
  import json

from nab.util import (absoluteFilePaths,
                      getProbationPeriod,
                      strf,
                      strp,
                      deepmap,
                      createPath,
                      writeJSON)



def bucket(rawTimes, buffer):
  """
  Buckets (groups) timestamps that are within the amount of time specified by
  buffer.
  """
  bucket = []
  rawBuckets = []

  current = None
  for t in rawTimes:
    if current is None:
      current = t
      bucket = [current]
      continue
    if (t - current) <= buffer:
      bucket.append(t)
    else:
      rawBuckets.append(bucket)
      current = t
      bucket = [current]
  if bucket:
    rawBuckets.append(bucket)

  return rawBuckets


def merge(rawBuckets, threshold):
  """
  Merges bucketed timestamps into one timestamp (most frequent, or earliest).
  """
  truths = []
  passed = []

  for bucket in rawBuckets:
    if len(bucket) >= threshold:
      truths.append(max(bucket, key=bucket.count))
    else:
      passed.append(bucket)

  return truths, passed


def checkForOverlap(labels, buffer, labelsFileName, dataFileName):
  """
  Raise a ValueError if the difference between any consecutive labels is smaller
  than the buffer.
  """
  for i in xrange(len(labels)-1):
    if labels[i+1] - labels[i] <= buffer:
      # import pdb; pdb.set_trace()
      raise ValueError("The labels {} and {} in \'{}\' labels for data file "
        "\'{}\' are too close to each other to be considered distinct "
        "anomalies. Please relabel."
        .format(labels[i], labels[i+1], labelsFileName, dataFileName))



class CorpusLabel(object):
  """
  Class to store and manipulate a single set of labels for the whole
  benchmark corpus.
  """

  def __init__(self, path, corpus):
    """
    Initializes a CorpusLabel object by getting the anomaly windows and labels.
    When this is done for combining raw user labels, we skip getLabels()
    because labels are not yet created.

    @param path    (string)      Name of file containing the set of labels.
    @param corpus  (nab.Corpus)  Corpus object.
    """
    self.path = path

    self.windows = None
    self.labels = None

    self.corpus = corpus
    self.getWindows()

    if "raw" not in self.path:
      # Do not get labels from files in the path nab/labels/raw
      self.getLabels()


  def getWindows(self):
    """
    Read JSON label file. Get timestamps as dictionaries with key:value pairs of
    a relative path and its corresponding list of windows.
    """
    def found(t, data):
      f = data["timestamp"][data["timestamp"] == pandas.Timestamp(t)]
      exists = (len(f) == 1)

      return exists

    with open(os.path.join(self.path)) as windowFile:
      windows = json.load(windowFile)

    self.windows = {}

    for relativePath in windows.keys():

      self.windows[relativePath] = deepmap(strp, windows[relativePath])

      if len(self.windows[relativePath]) == 0:
        continue

      data = self.corpus.dataFiles[relativePath].data
      if "raw" in self.path:
        timestamps = windows[relativePath]
      else:
        timestamps = list(itertools.chain.from_iterable(windows[relativePath]))

      # Check that timestamps are present in dataset
      if not all([found(t,data) for t in timestamps]):
        raise ValueError("In the label file %s, one of the timestamps used for "
                         "the datafile %s doesn't match; it does not exist in "
                         "the file. Timestamps in json label files have to "
                         "exactly match timestamps in corresponding datafiles."
                         % (self.path, relativePath))


  def validateLabels(self):
    """
    This is run at the end of the label combining process (see
    scripts/combine_labels.py) to validate the resulting ground truth windows,
    specifically that they are distinct (unique, non-overlapping).
    """
    with open(os.path.join(self.path)) as windowFile:
      windows = json.load(windowFile)

    self.windows = {}

    for relativePath in windows.keys():

      self.windows[relativePath] = deepmap(strp, windows[relativePath])

      if len(self.windows[relativePath]) == 0:
        continue

      num_windows = len(self.windows[relativePath])
      if num_windows > 1:
        if not all([(self.windows[relativePath][i+1][0]
                    - self.windows[relativePath][i][1]).total_seconds() >= 0
                    for i in xrange(num_windows-1)]):
          raise ValueError("In the label file %s, windows overlap." % self.path)


  def getLabels(self):
    """
    Get Labels as a dictionary of key-value pairs of a relative path and its
    corresponding binary vector of anomaly labels. Labels are simply a more
    verbose version of the windows.
    """
    self.labels = {}

    for relativePath, dataSet in self.corpus.dataFiles.iteritems():
      if self.windows.has_key(relativePath):
        windows = self.windows[relativePath]

        labels = pandas.DataFrame({"timestamp": dataSet.data["timestamp"]})
        labels['label'] = 0

        for t1, t2 in windows:
          moreThanT1 = labels[labels["timestamp"] >= t1]
          betweenT1AndT2 = moreThanT1[moreThanT1["timestamp"] <= t2]
          indices = betweenT1AndT2.loc[:,"label"].index
          labels["label"].values[indices.values] = 1

        self.labels[relativePath] = labels

      else:
        print "Warning: no label for datafile",relativePath


class LabelCombiner(object):
  """
  This class is used to combine labels from multiple human labelers, and the set
  of manual labels (known anomalies).
  The output is a single ground truth label file containing anomalies where
  there is enough human agreement. The class also computes the window around
  each anomaly.  The exact logic is described elsewhere in the NAB
  documentation.
  """

  def __init__(self, labelDir, corpus,
                     threshold, windowSize,
                     probationaryPercent, verbosity):
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
    @param windowSize (float)    Estimated size of an anomaly window, as a
                                 ratio the dataset length.
    @param verbosity  (int)      0, 1, or 2 to print out select labeling
                                 metrics; 0 is none, 2 is the most.
    """
    self.labelDir = labelDir
    self.corpus = corpus
    self.threshold = threshold
    self.windowSize = windowSize
    self.probationaryPercent = probationaryPercent
    self.verbosity = verbosity

    self.userLabels = None
    self.nLabelers = None
    self.knownLabels = None

    self.combinedWindows = None


  def __str__(self):
    ans = ""
    ans += "labelDir:            %s\n" % self.labelDir
    ans += "corpus:              %s\n" % self.corpus
    ans += "number of labelers:  %d\n" % self.nLabelers
    ans += "agreement threshold: %d\n" % self.threshold
    return ans


  def write(self, labelsPath, windowsPath):
    """Write the combined labels and windows to destination directories."""
    if not os.path.isdir(labelsPath):
      createPath(labelsPath)
    if not os.path.isdir(windowsPath):
      createPath(windowsPath)

    writeJSON(labelsPath, self.labelTimestamps)
    writeJSON(windowsPath, self.combinedWindows)


  def combine(self):
    """Combine raw and known labels in anomaly windows."""
    self.getRawLabels()
    self.combineLabels()
    self.editPoorLabels()
    self.applyWindows()
    self.checkWindows()


  def getRawLabels(self):
    """Collect the raw user labels from specified directory."""
    labelPaths = absoluteFilePaths(self.labelDir)
    self.userLabels = []
    self.knownLabels = []
    for path in labelPaths:
      if "known" in path:
        self.knownLabels.append(CorpusLabel(path, self.corpus))
      else:
        self.userLabels.append(CorpusLabel(path, self.corpus))

    self.nLabelers = len(self.userLabels)
    if self.nLabelers == 0:
      raise ValueError("No users labels found")


  def combineLabels(self):
    """
    Combines raw user labels to create set of true anomaly labels.
    A buffer is used to bucket labels that identify the same anomaly. The buffer
    is half the estimated window size of an anomaly -- approximates an average
    of two anomalies per dataset, and no window can have > 1 anomaly.
    After bucketing, a label becomes a true anomaly if it was labeled by a
    proportion of the users greater than the defined threshold. Then the bucket
    is merged into one timestamp -- the ground truth label.
    The set of known anomaly labels are added as well. These have been manually
    labeled because we know the direct causes of the anomalies. They are added
    as if they are the result of the bucket-merge process.

    If verbosity > 0, the dictionary passedLabels -- the raw labels that did not
    pass the threshold qualification -- is printed to the console.
    """
    def setTruthLabels(dataSet, trueAnomalies):
      """Returns the indices of the ground truth anomalies for a data file."""
      timestamps = dataSet.data["timestamp"]
      labels = numpy.array(timestamps.isin(trueAnomalies), dtype=int)
      return [i for i in range(len(labels)) if labels[i]==1]

    self.labelTimestamps = {}
    self.labelIndices = {}
    for relativePath, dataSet in self.corpus.dataFiles.iteritems():
      if ("Known" in relativePath) or ("artificial" in relativePath):
        knownAnomalies = self.knownLabels[0].windows[relativePath]
        self.labelTimestamps[relativePath] = [str(t) for t in knownAnomalies]
        self.labelIndices[relativePath] = setTruthLabels(dataSet, knownAnomalies)
        continue

      # Calculate the window buffer -- used for bucketing labels identifying
      # the same anomaly.
      granularity = dataSet.data["timestamp"][1] - dataSet.data["timestamp"][0]
      buffer = datetime.timedelta(minutes=
        granularity.total_seconds()/60 * len(dataSet.data) * self.windowSize/10)

      rawTimesLists = []
      userCount = 0
      for user in self.userLabels:
        if relativePath in user.windows:
          # the user has labels for this file
          checkForOverlap(
            user.windows[relativePath], buffer, user.path, relativePath)
          rawTimesLists.append(user.windows[relativePath])
          userCount += 1
      if not rawTimesLists:
        # no labeled anomalies for this data file
        self.labelTimestamps[relativePath] = []
        self.labelIndices[relativePath] = setTruthLabels(dataSet, [])
        continue
      else:
        rawTimes = list(itertools.chain.from_iterable(rawTimesLists))
        rawTimes.sort()

      # Bucket and merge the anomaly timestamps.
      threshold = userCount * self.threshold
      trueAnomalies, passedAnomalies = merge(
        bucket(rawTimes, buffer), threshold)

      self.labelTimestamps[relativePath] = [str(t) for t in trueAnomalies]
      self.labelIndices[relativePath] = setTruthLabels(dataSet, trueAnomalies)

      if self.verbosity>0:
        print "----"
        print "For %s the passed raw labels and qualified true labels are,"\
              " respectively:" % relativePath
        print passedAnomalies
        print trueAnomalies

    return self.labelTimestamps, self.labelIndices


  def editPoorLabels(self):
    """
    This edits labels that have been flagged for manual revision. From
    inspecting the data and anomaly windows, we have determined some combined
    labels should be revised, or not included in the ground truth labels.
    """
    count = 0
    for relativePath, indices in self.labelIndices.iteritems():

      if "iio_us-east-1_i-a2eb1cd9_NetworkIn" in relativePath:
        self.labelIndices[relativePath] = [249, 339]

      count += len(indices)

    if self.verbosity > 0:
      print "============================================================="
      print "Total ground truth anomalies in benchmark dataset =", count


  def applyWindows(self):
    """
    This takes all the true anomalies, as calculated by combineLabels(), and
    adds a standard window. The window length is the class variable windowSize,
    and the location is centered on the anomaly timestamp.

    If verbosity = 2, the window metrics are printed to the console.
    """
    allWindows = {}
    for relativePath, anomalies in self.labelIndices.iteritems():
      data = self.corpus.dataFiles[relativePath].data
      length = len(data)
      num = len(anomalies)
      if num:
        windowLength = int(self.windowSize * length / len(anomalies))
      else:
        windowLength = int(self.windowSize * length)

      if self.verbosity==2:
        print "----"
        print "Window metrics for file", relativePath
        print "file length =", length, ";" \
              "number of windows =", num, ";" \
              "window length =", windowLength

      windows = []
      for a in anomalies:
        front = max(a - windowLength/2, 0)
        back = min(a + windowLength/2, length-1)

        windowLimit = [strf(data["timestamp"][front]),
                       strf(data["timestamp"][back])]

        windows.append(windowLimit)

      allWindows[relativePath] = windows

    self.combinedWindows = allWindows


  def checkWindows(self):
    """
    This takes the anomaly windows and checks for overlap with both each other
    and with the probationary period. Overlapping windows are merged into a
    single window. Windows overlapping with the probationary period are deleted.
    """
    for relativePath, windows in self.combinedWindows.iteritems():
      numWindows = len(windows)
      if numWindows > 0:

        fileLength = self.corpus.dataFiles[relativePath].data.shape[0]
        probationIndex = getProbationPeriod(
          self.probationaryPercent, fileLength)

        probationTimestamp = self.corpus.dataFiles[relativePath].data[
          "timestamp"][probationIndex]

        if (pandas.to_datetime(windows[0][0])
            -probationTimestamp).total_seconds() < 0:
          del windows[0]
          print ("The first window in {} overlaps with the probationary period "
                 ", so we're deleting it.".format(relativePath))

        i = 0
        while len(windows)-1 > i:
          if (pandas.to_datetime(windows[i+1][0])
              - pandas.to_datetime(windows[i][1])).total_seconds() <= 0:
            # merge windows
            windows[i] = [windows[i][0], windows[i+1][1]]
            del windows[i+1]
          i += 1
