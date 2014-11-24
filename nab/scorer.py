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
  """Class to store a single window in a datafile."""

  def __init__(self, windowId, limits, data):
    """
    @param windowId   (int)           An integer id for the window.

    @limits           (tuple)         (start timestamp, end timestamp).

    @allRecords       (pandas.Series) Raw rows of the whole datafile.
    """
    self.id = windowId
    self.t1, self.t2 = limits

    tmp = data[data["timestamp"] >= self.t1]
    self.window = tmp[tmp["timestamp"] <= self.t2]

    self.indices = self.window.index
    self.length = len(self.indices)


  def __repr__(self):
    """
    String representation of Window. For debugging.
    """
    s = "WINDOW id=" + str(self.id)
    s += ", limits: [" + str(self.t1) + ", " + str(self.t2) + "]"
    s += ", length: " + str(self.length)
    s += "\nwindow data:\n" + str(self.window)
    return s


  def getFirstTruePositive(self):
    """Get the index of the first true positive within a window.

    @return (int)   Index of the first occurrence of the true positive within
                    the window. -1 if there are none.
    """
    tp = self.window[self.window["type"] == "tp"]
    if len(tp) > 0:
      return tp.iloc[0].name
    else:
      return -1


class Scorer(object):
  """Class used to score a datafile."""

  def __init__(self,
               timestamps,
               predictions,
               labels,
               windowLimits,
               costMatrix,
               probationaryPeriod):
    """
    @param predictions   (pandas.Series)   Detector predictions of
                                           whether each record is anomalous or
                                           not. predictions[
                                           0:probationaryPeriod] is ignored.

    @param labels        (pandas.DataFrame) Ground truth for each record.
                                           For each record there should be a 1
                                           or a 0. A 1 implies this record is
                                           within an anomalous window.

    @param windowLimits  (list)            All the window limits in tuple
                                           form: (timestamp start, timestamp
                                           end).

    @param costmatrix    (dict)            Dictionary containing the
                                           cost matrix for this profile.
                                           type:  True positive (tp)
                                                  False positive (fp)
                                                  True Negative (tn)
                                                  False Negative (fn)

    @param probationaryPeriod
                         (int)             Row index after which predictions
                                           are scored.
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
    """Create list of windows for this datafile.

    @return (list)    All the window limits in tuple form: (timestamp start,
                      timestamp end).
    """
    #SORT WINDOWS BEFORE PUTTING THEM IN LIST
    windows = [Window(i, limit, self.data) for i, limit in enumerate(limits)]
    return windows


  def getAlertTypes(self, predictions):
    """For each record, decide whether it is a tp, fp, tn, or fn. Populate
    counts dictionary with the total number of records in each category.
    Return a list of strings containing each prediction type."""
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
    """Score the entire datafile and return a single floating point score.

    @return (float)    Quantified score for the given datafile.
    """
    # Calculate the score for each window. Each window will either have one or
    # more true positives or no predictions (i.e. a false negative). FNs
    # lead to a negative contribution, TPs a positive one.
    tpScore = 0
    fnScore = 0
    for window in self.windows:

      tpIndex = window.getFirstTruePositive()

      if tpIndex == -1:
        fnScore -= self.costMatrix["fnWeight"]
      else:
        if window.length <= 1:
          newdist = -2.0
        else:
          newdist = -(window.indices[-1] - tpIndex)/float(window.length-1)

        tpScore += scaledSigmoid(newdist)*self.costMatrix["tpWeight"]

    # Go through each false positive and score it. Each FP leads to a negative
    # contribution dependent on how far it is from the previous window.
    fpLabels = self.data[self.data["type"] == "fp"]
    fpScore = 0
    for i in fpLabels.index:
      windowId = self.getClosestPrecedingWindow(i)

      if windowId == -1:
        fpScore -= self.costMatrix["fpWeight"]
      else:
        window = self.windows[windowId]

        if window.length <= 1:
          newdist = 2.0
        else:
          newdist = abs(window.indices[-1] - i)/float(window.length-1)

        fpScore += scaledSigmoid(newdist)*self.costMatrix["fpWeight"]

    self.score = tpScore + fpScore + fnScore

    return self.score


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
  """Standard sigmoid function."""
  return 1 / (1 + math.exp(-x))


def scaledSigmoid(relativePositionInWindow):
  """Return a scaled sigmoid function given a relative position within a
  labeled window.  The function is computed as follows:

  A relative position of -1.0 is the far left edge of the anomaly window and
  corresponds to a 2*sigmoid(5) - 1.0 = 0.98661.  This is as early as you can
  get and still get counted as a true positive.

  A relative position of -0.5 is halfway into the anomaly window and
  corresponds to a 2*sigmoid(0.5*5) - 1.0 = 0.84828.

  A relative position of 0.0 consists of the right edge of the window and
  corresponds to a score of 2*sigmoid(0) - 1 = 0.0

  Relative positions > 0 correspond to false positives increasingly far away
  from the right edge of the window. A relative position of 1.0 is past the
  right  edge of the  window and corresponds to a score of 2*sigmoid(-5) - 1.0 =
  -0.98661

  @param  relativePositionInWindow (float)  A relative position
                                            within a window calculated per the
                                            rules above.

  @return (float)
  """
  if relativePositionInWindow > 3.0:
    return -1.0
  elif relativePositionInWindow < -3.0:
    return 1.0
  else:
    return 2*sigmoid(-5*relativePositionInWindow) - 1.0


def scoreCorpus(threshold, args):
  """Given a score to the corpus given a detector and a user profile.

  Scores the corpus in parallel.

  @param threshold  (float)   Threshold value to convert an anomaly score value
                              to a detection.

  @param args (tuple) Contains:
    pool                (multiprocessing.Pool)  Pool of processes to perform
                                                perform tasks in parallel.

    costMatrix          (dict)                  Cost matrix to weight the
                                                true positives, false negatives,
                                                and false positives during
                                                scoring.

    resultsCorpus       (nab.Corpus)            Corpus object that holds the per
                                                record anomaly scores for a
                                                given detector.

    corpusLabel         (nab.CorpusLabel)       Ground truth anomaly labels for
                                                the nab corpus.

    probationaryPercent (float)                 Percent of each data file not
                                                to be considered during scoring.
  """
  (pool,
   costMatrix,
   resultsCorpus,
   corpusLabel,
   probationaryPercent) = args

  args = []
  for relativePath, dataSet in resultsCorpus.dataFiles.iteritems():
    if "_scores.csv" in relativePath:
      continue

    relativePath = convertResultsPathToDataPath(
      os.path.join(relativePath))

    windows = corpusLabel.windows[relativePath]
    labels = corpusLabel.labels[relativePath]

    probationaryPeriod = math.floor(probationaryPercent * labels.shape[0])

    predicted = convertAnomalyScoresToDetections(
      dataSet.data["anomaly_score"], threshold)

    args.append((
      relativePath,
      predicted,
      windows,
      labels,
      costMatrix,
      probationaryPeriod))

  results = pool.map(scoreDataSet, args)

  totals = [0] * (len(results[0]) - 1)

  for row in results:
    for i in range(len(totals)):
      totals[i] += row[i + 1]

  results.append(["Totals"] + totals)

  resultsDataFrame = pandas.DataFrame(data=results,
    columns=("File", "Score", "tpCount", "tnCount", "fpCount", "fnCount",
      "TotalCount"))

  resultsDataFrame = resultsDataFrame.convert_objects()

  return resultsDataFrame


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
  (relativePath,
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

  return (relativePath, scorer.score, counts["tp"], counts["tn"], counts["fp"],
    counts["fn"], scorer.length)
