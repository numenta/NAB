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
    self.tp = dictionary["tpCost"]
    self.tn = dictionary["tnCost"]
    self.fp = dictionary["fpCost"]
    self.fn = dictionary["fnCost"]
    self.values = dictionary


class Window(object):
  """
  Class to store a window in a dataset
  """

  def __init__(self, windowId, limits, labels):
    self.id = windowId
    self.t1, self.t2 = limits
    self.indices = self.getIndices(labels)
    self.labels = labels
    self.length = len(self.indices)
    self.firstTP = self.getFirstTP()


  def getIndices(self, labels):
    """
    Given a set of labels, get the pandas index of the records within the window
    """
    tmp = labels[labels["timestamp"] >= self.t1]
    windows = tmp[tmp["timestamp"] <= self.t2]
    return windows.index

  def getFirstTP(self):
    """
    Get the first instance of True positive within a window if it exists.
    Otherwise, return -1
    """
    tp = self.labels[self.labels["type"] == "tp"]
    if len(tp):
      return tp.iloc[0].name
    return -1


class Scorer(object):
  """
  Class used to score a dataset
  """
  def __init__(self, predicted, labels, windowLimits, costMatrix, probationaryPeriod):
    self.predicted = predicted
    self.labels = labels
    self.probationaryPeriod = probationaryPeriod
    self.costMatrix = CostMatrix(costMatrix)
    self.counts = None
    self.totalCount = None
    self.score = None

    self.initCount()
    self.windows = self.getWindows(windowLimits)


  def initCount(self):
    """
    Initialize dictionary that counts the number of tp's, tn's, fp's, and fn's
    """
    self.counts = {
    "tp": 0,
    "tn": 0,
    "fp": 0,
    "fn": 0}

    self.totalCount = len(self.predicted)


  def getWindows(self, limits):
    """
    Create list of windows of the dataset
    """
    #SORT WINDOWS BEFORE PUTTING THEM IN LIST

    self.getLabelTypes()
    ans = [Window(i,limits[i],self.labels) for i in range(len(limits))]
    return ans


  def getLabelTypes(self):
    """
    Populate counts dictionary
    """
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
    """
    Score the dataset
    """

    # collect TP scores
    tpScore = 0
    for window in self.windows:
      tpIndex = window.getFirstTP()
      if tpIndex == -1:
        tpScore -= 100
      else:
        dist = (window.indices[-1] - tpIndex)/window.length
        tpScore += (2*sigmoid(dist) - 0.5)*self.costMatrix.tp


    # collect FP scores
    fpLabels = self.labels[self.labels["type"] == "fp"]
    fpScore = 0
    for i, row in fpLabels.iterrows():
      windowId = self.getClosestPrecedingWindow(i)
      if windowId == -1:
        fpScore -= 1
        continue

      window = self.windows[windowId]
      fpScore -= (sigmoid((window.indices[-1] - tpIndex)/window.length) - 0.5)*self.costMatrix.fp

    score = tpScore + fpScore
    self.score = score

    return score




  def getClosestPrecedingWindow(self, index):
    """
    given a record index, find the closest preceding window. This helps score
    false positives.
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
  """
  Monotonically decreasing function used to score true positives and false
  positives.
  """
  return 1 / (1 + math.exp(-x))
