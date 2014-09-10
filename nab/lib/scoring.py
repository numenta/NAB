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

import math



class CostMatrix(object):
  """
  Class to store a costmatrix
  """
  def __init__(self, dictionary):
    """
    @param (dict)     Dictionary containing all the weights for each record
                      type: True positive (tp)
                            False positive (fp)
                            True Negative (tn)
                            False Negative (fn)
    """
    self.tp = dictionary["tpCost"]
    self.tn = dictionary["tnCost"]
    self.fp = dictionary["fpCost"]
    self.fn = dictionary["fnCost"]
    self.values = dictionary


class Window(object):
  """Class to store a window in a dataset."""

  def __init__(self, windowId, limits, labels):
    """
    @param windowId   (int)           An integer id for the window.

    @limits           (tuple)         (start timestamp, end timestamp).

    @labels           (pandas.Series) Raw rows of the data within the window.
    """
    self.id = windowId
    self.t1, self.t2 = limits
    self.indices = self.getIndices(labels)
    self.labels = labels
    self.length = len(self.indices)
    self.firstTP = self.getFirstTP()


  def getIndices(self, labels):
    """Given a set of labels, get the pandas index of the records within window.

    @param    labels  (pandas.Series)                 Raw rows of the data
                                                      within the window.

    @return           (pandas.core.index.Int64Index)  Row indices of the labels
                                                      within the window.
    """
    tmp = labels[labels["timestamp"] >= self.t1]
    windows = tmp[tmp["timestamp"] <= self.t2]
    return windows.index

  def getFirstTP(self):
    """Get the first instance of True positive within a window.

    @return (int)   Index of the first occurence of the true positive within the
                    window.
    """
    tp = self.labels[self.labels["type"] == "tp"]
    if len(tp):
      return tp.iloc[0].name
    return -1


class Scorer(object):
  """Class used to score a dataset."""

  def __init__(self,
               predicted,
               labels,
               windowLimits,
               costMatrix,
               probationaryPeriod):
    """
    @param predicted           (pandas.Series)   Detector predictions of whether
                                                 each record is anomalous or not.
                                                 predictions[0:probationaryPeriod]
                                                 is ignored.

    @param labels              (pandas.Series)   Ground truth for each record.

    @param windowLimits        (list)            All the window limits in tuple
                                                 form: (timestamp start, timestamp
                                                 end).

    @param costmatrix          (dict)            Dictionary containing all the weights for each record
                                                 type:  True positive (tp)
                                                        False positive (fp)
                                                        True Negative (tn)
                                                        False Negative (fn)

    @param probationaryPeriod  (int)             Row index after which predictions
                                                 are scored.
    """
    self.predicted = predicted
    self.labels = labels
    self.probationaryPeriod = probationaryPeriod
    self.costMatrix = costMatrix
    self.totalCount = len(self.predicted)

    self.counts = {
    "tp": 0,
    "tn": 0,
    "fp": 0,
    "fn": 0}

    self.score = None

    self.windows = self.getWindows(windowLimits)


  def getWindows(self, limits):
    """Create list of windows of the dataset.

    @return (list)    All the window limits in tuple form: (timestamp start,
                      timestamp end).
    """
    #SORT WINDOWS BEFORE PUTTING THEM IN LIST
    self.getAlertTypes()
    windows = [Window(i,limits[i], self.labels) for i in range(len(limits))]
    return windows


  def getAlertTypes(self):
    """Populate counts dictionary."""
    types = []

    for i, row in self.labels.iterrows():
      if i < self.probationaryPeriod:
        types.append("probationaryPeriod")
        continue

      pred = self.predicted[int(i)]
      diff = abs(pred - row["label"])
      category = ""
      category += "f" if bool(diff) else "t"
      category += "p" if bool(self.predicted[int(i)]) else "n"
      self.counts[category] += 1
      types.append(category)

    self.labels["type"] = types


  def getScore(self):
    """Score the dataset.

    @return (float)    Quantified score for the given dataset.
    """
    tpScore = 0
    fnScore = 0
    for window in self.windows:
      tpIndex = window.getFirstTP()
      if tpIndex == -1:
        fnScore +=self.costmatrix["fnWeight"]
      else:
        dist = (window.indices[-1] - tpIndex)/window.length
        tpScore += (2*sigmoid(dist) - 0.5)*self.costMatrix["tpWeight"]

    fpLabels = self.labels[self.labels["type"] == "fp"]
    fpScore = 0
    for i, _ in fpLabels.iterrows():
      windowId = self.getClosestPrecedingWindow(i)
      if windowId == -1:
        fpScore += self.costmatrix["fpWeight"]
        continue

      window = self.windows[windowId]

      dist = (window.indices[-1] - tpIndex)/window.length
      fpScore += (sigmoid(dist) - 0.5)*self.costMatrix["fpWeight"]

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
