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
import pandas
from nab.util import (convertResultsPathToDataPath,
                      convertAnomalyScoresToDetections)
import math



class Window(object):
  """Class to store a window in a dataset."""

  def __init__(self, windowId, limits, data):
    """
    @param windowId   (int)           An integer id for the window.

    @limits           (tuple)         (start timestamp, end timestamp).

    @allRecords       (pandas.Series) Raw rows of the the whole dataset.
    """
    self.id = windowId
    self.t1, self.t2 = limits

    tmp = labels[labels["timestamp"] >= self.t1]
    self.window = tmp[tmp["timestamp"] <= self.t2]

    self.indices = self.window.index
    self.length = len(self.indices)


  def getFirstTruePositive(self):
    """Get the first instance of True positive within a window.

    @return (int)   Index of the first occurence of the true positive within the
                    window.
    """
    tp = self.window[self.window["type"] == "tp"]
    if len(tp):
      return tp.iloc[0].name
    return -1


class Scorer(object):
  """Class used to score a dataset."""

  def __init__(self,
               timestamps,
               predictions,
               labels,
               windowLimits,
               costMatrix,
               probationaryPeriod):
    """
    @param predictions           (pandas.Series)   Detector predictions of whether
                                                 each record is anomalous or
                                                 not.
                                                 predictions[
                                                 0:probationaryPeriod]
                                                 is ignored.

    @param labels              (pandas.Series)   Ground truth for each record.

    @param windowLimits        (list)            All the window limits in tuple
                                                 form: (timestamp start,
                                                 timestamp end).

    @param costmatrix          (dict)            Dictionary containing all the
                                                 weights for each record
                                                 type:  True positive (tp)
                                                        False positive (fp)
                                                        True Negative (tn)
                                                        False Negative (fn)

    @param probationaryPeriod  (int)             Row index after which
                                                 predictions are scored.
    """
    self.data = pandas.DataFrame()
    self.data["timestamp"] = timestamps
    self.data["label"] = labels

    self.probationaryPeriod = probationaryPeriod
    self.costMatrix = costMatrix
    self.totalCount = len(self.data["label"])

    self.counts = {
      "tp": 0,
      "tn": 0,
      "fp": 0,
      "fn": 0}

    self.score = None
    self.length = len(predictions)
    self.data["type"] = self.getAlertTypes(predictions)
    self.windows = self.getWindows(windowLimits)


  def getWindows(self, limits):
    """Create list of windows of the dataset.

    @return (list)    All the window limits in tuple form: (timestamp start,
                      timestamp end).
    """
    #SORT WINDOWS BEFORE PUTTING THEM IN LIST
    windows = [Window(i, limit, self.data) for i, limit in enumerate(limits)]
    return windows


  def getAlertTypes(self, predictions):
    """Populate counts dictionary."""
    types = []

    for i, row in self.data.iterrows():
      if i < self.probationaryPeriod:
        types.append("probationaryPeriod")
        continue

      pred = predictions[int(i)]
      diff = abs(pred - row["label"])

      category = str()
      category += "f" if bool(diff) else "t"
      category += "p" if bool(pred) else "n"
      self.counts[category] += 1
      types.append(category)

    return types


  def getScore(self):
    """Score the dataset.

    @return (float)    Quantified score for the given dataset.
    """
    tpScore = 0
    fnScore = 0
    for window in self.windows:
      tpIndex = window.getFirstTruePositive()
      if tpIndex == -1:
        fnScore += self.costMatrix["fnWeight"]
      else:
        dist = (window.indices[-1] - tpIndex)/self.length
        tpScore += (2*sigmoid(dist) - 1)*self.costMatrix["tpWeight"]

    fpLabels = self.data[self.data["type"] == "fp"]
    fpScore = 0
    for i, _ in fpLabels.iterrows():
      windowId = self.getClosestPrecedingWindow(i)
      if windowId == -1:
        fpScore += self.costMatrix["fpWeight"]
        continue

      window = self.windows[windowId]

      dist = (window.indices[-1] - tpIndex)/self.length
      fpScore += (2*sigmoid(dist) - 1)*self.costMatrix["fpWeight"]

    score = tpScore - fpScore - fnScore
    self.score = score

    return score


  def getClosestPrecedingWindow(self, index):
    """Given a record index, find the closest preceding window.

    This helps score false positives.

    @param  index   (int)   Index of a record.

    @return         (int)   Window id for the last window preceding the given
                            index.
    """
    minDistance = float("inf")
    windowId = -1
    for window in self.windows:
      if window.indices[-1] < index:
        dist = index - window.indices[-1]
        if dist < minDistance:
          minDistance = dist
          windowId = window.id

    return windowId


def sigmoid(x):
  """Monotonically decreasing function used to score.

  @param  (float)

  @return (float)
  """
  return 1 / (1 + math.exp(-x))

def scoreCorpus(threshold, args):
  """Given a score to the corpus given a detector and a user profile.

  Scores the corpus in parallel.

  @param threshold  (float)   Threshold value to convert an anomaly score value
                              to a detection.

  @param args       (tuple)   Arguments necessary to call scoreHelper
  """
  (pool,
   detector,
   username,
   costMatrix,
   resultsCorpus,
   corpusLabel,
   probationaryPercent) = args

  args = []
  for relativePath, dataSet in resultsCorpus.dataSets.iteritems():
    if relativePath == detector + "_scores.csv":
      continue

    relativePath = convertResultsPathToDataPath( \
      os.path.join(detector, relativePath))

    windows = corpusLabel.windows[relativePath]
    labels = corpusLabel.labels[relativePath]

    probationaryPeriod = math.floor(
      probationaryPercent * labels.shape[0])

    predicted = convertAnomalyScoresToDetections(
      dataSet.data["anomaly_score"], threshold)

    args.append((
      detector,
      username,
      relativePath,
      threshold,
      predicted,
      windows,
      labels,
      costMatrix,
      probationaryPeriod))

  results = pool.map(scoreDataSet, args)

  return results


def scoreDataSet(args):
  """Function called to score each dataset in the corpus.

  @param args   (tuple)  Arguments to get the detection score for a dataset.

  @return       (tuple)  Contains:
    detectorName  (string)  Name of detector used to get anomaly scores.

    username      (string)  Name of profile used to weight each detection type.
                            (tp, tn, fp, fn)

    relativePath  (string)  Path of dataset scored.

    threshold     (float)   Threshold used to convert anomaly scores to
                            detections.

    score         (float)   The score of the dataset.

    counts, tp    (int)     The number of true positive records.

    counts, tn    (int)     The number of true negative records.

    counts, fp    (int)     The number of false positive records.

    counts, fn    (int)     The number of false negative records.

    Total count   (int)     The total number of records.
  """
  (detectorName,
   username,
   relativePath,
   threshold,
   predicted,
   windows,
   labels,
   costMatrix,
   probationaryPeriod) = args

  scorer = Scorer(
    timestamps=labels["timestamp"],
    predictions=predicted,
    labels=labels["label"],
    windowLimits=windows,
    costMatrix=costMatrix,
    probationaryPeriod=probationaryPeriod)

  scorer.getScore()

  counts = scorer.counts

  return (detectorName, username, relativePath, threshold, scorer.score, \
  counts["tp"], counts["tn"], counts["fp"], counts["fn"], \
  scorer.length)
