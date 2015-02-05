# ----------------------------------------------------------------------
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
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
                      strf,
                      strp,
                      deepmap,
                      createPath)



class CorpusLabel(object):
  """
  Class to store and manipulate a single set of labels for the whole
  benchmark corpus.
  """

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
    Read JSON label file. Get windows as dictionaries with key value pairs of a
    relative path and its corresponding list of windows.
    """
    def found(t, data):
      f = data["timestamp"][data["timestamp"] == pandas.tslib.Timestamp(t)]
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

      timestamps = list(itertools.chain(windows[relativePath]))[0]

      # Check that windows are in dataset timestamps
      if not all([found(t,data) for t in timestamps]):
        raise ValueError("In the label file %s, one of the timestamps used for "
                         "the datafile %s doesn't match; it does not exist in "
                         "the file. Timestamps in json label files have to "
                         "exactly match timestamps in corresponding datafiles."
                         % (self.path, relativePath))
      
      # Check that window timestamps are chronological
      deltas = [(pandas.to_datetime(timestamps[i+1])
                 - pandas.to_datetime(timestamps[i])).total_seconds() >= 0
                for i in range(len(timestamps)-1)]

      if not all(deltas):
        raise ValueError("In the label file %s, timestamps are not in "
                         "chronological order." % self.path)
      
      # Check that windows are distinct (unique, non-overlapping); the end time
      # of a window can be the same as the start time of the subsequent window.
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
      windows = self.windows[relativePath]

      labels = pandas.DataFrame({"timestamp": dataSet.data["timestamp"]})
      labels['label'] = 0

      for t1, t2 in windows:
        moreThanT1 = labels[labels["timestamp"] >= t1]
        betweenT1AndT2 = moreThanT1[moreThanT1["timestamp"] <= t2]
        indices = betweenT1AndT2.loc[:,"label"].index
        labels["label"].values[indices.values] = 1

      self.labels[relativePath] = labels


class LabelCombiner(object):
  """
  This class is used to combine labels from multiple human labelers. The output
  is a single ground truth label file containing anomalies where there is
  enough human agreement. The class also computes the window around each
  anomaly.  The exact logic is described elsewhere in the NAB documentation.
  """

  def __init__(self, labelDir, corpus, threshold=0.5,
                                       windowSize=0.10,
                                       verbosity=1):
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
    self.verbosity = verbosity

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
    if not os.path.isdir(destPath):
      createPath(destPath)
    windows = json.dumps(self.combinedWindows,
      sort_keys=True, indent=4, separators=(',', ': '))
    with open(destPath, "w") as windowWriter:
      windowWriter.write(windows)


  def combine(self):
    """Combine the raw user labels, and set the anomaly windows."""
    self.getUserLabels()
    self.combineRawLabels()
    self.applyWindows()
    self.checkWindows()
    self.addKnownLabels()


  def getUserLabels(self):
    """Collect the raw user labels from default labels directory."""
    labelPaths = absoluteFilePaths(self.labelDir)

    self.userLabels = [CorpusLabel(path, self.corpus) for path in labelPaths]

    if len(self.userLabels) == 0:
      raise ValueError("No users labels found")

    self.nlabelers = len(self.userLabels)

    
  def combineRawLabels(self):
    """
    Combines raw user labels to create set of true anomaly labels; checks 
    explicitly for common start times in the raw windows.
    A buffer is used to merge labels that identify the same anomaly. The buffer
    is half the estimated window size of an anomaly -- approximates an average
    of two anomalies per dataset, and no window can have >1 anomaly.
    After merging, a label becomes a true anomaly if it was labeled by a
    proportion of the users greater than the defined threshold.
    
    If verbosity>0, the dictionary passedLabels -- the raw labels that did not
    pass the threshold qualification -- is printed to the console.
    """
    combinedLabels = {}
    labelIndices = {}
    passedLabels = {}
    
    for relativePath, dataSet in self.corpus.dataFiles.iteritems():
      
      length = len(dataSet.data)
      timestamps = dataSet.data["timestamp"]
      buffer = datetime.timedelta(minutes=round(length*self.windowSize/2))
      rawWindows = []
      bucket = []
      rawAnomalies = []
      trueAnomalies = []
      passedAnomalies = []
      
      for user in self.userLabels:
        if user.windows[relativePath]:
          rawWindows.append(user.windows[relativePath])
      if not rawWindows:
          # No labeled anomalies in this dataset
          combinedLabels[relativePath] = pandas.DataFrame(
            {"timestamp":timestamps, "label":numpy.zeros(length, dtype=int)})
          labelIndices[relativePath] = []
          continue
      else:
        times = []
        # Get all the labeled start times
        [times.append(t[0]) for timesList in rawWindows for t in timesList]
      times.sort()

      # Bucket similar timestamps
      current = None
      for t in times:
        if current is None:
          current = t
          bucket = [current]
          continue
        if (t - current) <= buffer:
          bucket.append(t)
        else:
          rawAnomalies.append(bucket)
          current = t
          bucket = [current]
      if bucket:
        rawAnomalies.append(bucket)

      # Merge the bucketed timestamps that qualify as true anomalies
      for bucket in rawAnomalies:
        if len(bucket) >= len(self.userLabels)*self.threshold:
          trueAnomalies.append(max(bucket, key=bucket.count))
        else:
          passedAnomalies.append(bucket)

      labels = numpy.array(timestamps.isin(trueAnomalies), dtype=int)
      combinedLabels[relativePath] = pandas.DataFrame(
        {"timestamp":timestamps, "label":labels})
      labelIndices[relativePath] = [i for i in range(len(labels))
                                    if labels[i]==1]
      passedLabels[relativePath] = passedAnomalies
      
      if self.verbosity>0:
        print "----"
        print "For %s the passed raw labels and qualified true labels are,"\
              " respectively:" % relativePath
        print passedAnomalies
        print trueAnomalies
  
    self.combinedLabels = combinedLabels
    self.labelIndices = labelIndices
    

  def applyWindows(self):
    """
    This takes all the true anomalies, as calculated by combineRawLabels(), and
    adds a standard window. The window length is the class variable windowSize,
    and the location is centered on the anomaly timestamp.
    
    If verbosity=2, the window metrics are printed to the console.
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
    This takes the anomaly windows and merges overlapping windows into a
    single window.
    """
    for relativePath, windows in self.combinedWindows.iteritems():
      num_windows = len(windows)
      if num_windows > 1:
        for i in range(num_windows-1):
          if (pandas.to_datetime(windows[i+1][0])
              - pandas.to_datetime(windows[i][1])).total_seconds() <= 0:
            windows[i] = [windows[i][0], windows[i+1][1]]
            del windows[i+1]


  def addKnownLabels(self):
    """
    Some data files in the benchmark dataset are of reported anomalies with
    known causes. These are added manually here.
    """




    pass
