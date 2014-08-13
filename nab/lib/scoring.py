from collections import defaultdict
import math
import sys

class CostMatrix(object):
  def __init__(self, dictionary):
    print dictionary
    self.tp = dictionary['tpCost']
    self.tn = dictionary['tnCost']
    self.fp = dictionary['fpCost']
    self.fn = dictionary['fnCost']
    self.values = dictionary


class Window(object):

  def __init__(self, windowId, limits, labels):
    self.id = windowId
    self.t1, self.t2 = limits
    self.indices = self.getIndices(labels)
    self.labels = labels
    self.length = len(self.indices)
    self.firstTP = self.getFirstTP()


  def getIndices(self, labels):
    tmp = labels[labels['timestamp'] >= self.t1]
    windows = tmp[tmp['timestamp'] <= self.t2]
    return windows.index

  def getFirstTP(self):
    tp = self.labels[self.labels['type'] == 'tp']
    if len(tp):
      return tp.iloc[0].name
    return -1

  def isInWindow(self, index):
    return index in self.indices



class Scorer(object):
  def __init__(self, predicted, labels, windowLimits, costMatrix, probationaryPeriod, options=None):
    self.predicted = predicted
    self.labels = labels
    self.count = defaultdict(int)
    self.probationaryPeriod = probationaryPeriod
    self.windows = self.getWindows(windowLimits)
    self.options = options
    self.costMatrix = CostMatrix(costMatrix)
    self.score = self.getScore()


  def getWindows(self, limits):
    #SORT WINDOWS BEFORE PUTTING THEM IN LIST
    self.getLabelTypes()
    return [Window(i,limits[i],self.labels) for i in range(len(limits))]


  def getLabelTypes(self):
    types = []

    for i, row in self.labels.iterrows():
      if i < self.probationaryPeriod:
        types.append('probationaryPeriod')
        continue

      pred = self.predicted[i]
      diff = abs(pred - row['label'])
      category = ''
      category += 'f' if bool(diff) else 't'
      category += 'p' if bool(self.predicted[i]) else 'n'
      self.count[category] += 1
      types.append(category)

    self.labels['type'] = types

  def getScore(self):

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
    fpLabels = self.labels[self.labels['type'] == 'fp']
    fpScore = 0
    for i, row in fpLabels.iterrows():
      windowId = self.getClosestPrecedingWindow(i)
      if windowId == -1:
        fpScore -= 1
        continue

      window = self.windows[windowId]
      fpScore -= (sigmoid((window.indices[-1] - tpIndex)/window.length) - 0.5)*self.costMatrix.fp


    score = tpScore + fpScore
    # print tpScore, fpScore, score
    return score

  def getClosestPrecedingWindow(self, index):
    minDistance = float('inf')
    windowId = -1
    for window in self.windows:
      if window.indices[-1] < index:
        dist = index - window.indices[-1]
        if dist < minDistance:
          minDistance = dist
          windowId = window.id

    return windowId


def sigmoid(x):
  return 1 / (1 + math.exp(-x))
