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
from collections import namedtuple
import logging
import math

from nab.corpus import Corpus
from nab.scorer import scaledSigmoid


AnomalyPoint = namedtuple("AnomalyPoint", ["timestamp", "anomalyScore", "SweepScore", "windowName"])
logger = logging.getLogger(__name__)



class Optimizer(object):
  def __init__(self, probationPercent=0.15, costMatrix=None):
    self.probationPercent = probationPercent

    self.tpWeight = None
    self.fpWeight = None
    self.fnWeight = None

    if costMatrix is not None:
      self.setCostMatrix(costMatrix)

  def setCostMatrix(self, costMatrix):
    self.tpWeight = costMatrix["tpWeight"]
    self.fpWeight = costMatrix["fpWeight"]
    self.fnWeight = costMatrix["fnWeight"]

  def optimizeCorpus(self):
    pass

  def optimizeFile(self):
    pass  # Probably not needed.

  def scoreCorpus(self):
    pass

  def scoreFile(self):
    pass

  def _getProbationaryLength(self, numRows):
    return min(math.floor(self.probationPercent * numRows), self.probationPercent * 5000)

  def calcSweepScore(self, timestamps, anomalyScores, windowLimits, dataSetName):
    assert len(timestamps) == len(anomalyScores), "timestamps and anomalyScores should not be different lengths!"
    # The final list of anomaly points returned from this function.
    # Used for threshold optimization and scoring in other functions.
    anomalyList = []

    # One-time config variables
    maxTP = scaledSigmoid(-1.0)
    probationaryLength = self._getProbationaryLength(len(timestamps))

    # Iteration variables - these update as we  iterate through the data
    curWindowLimits = None
    curWindowName = None
    curWindowWidth = None
    curWindowRightIndex = None
    prevWindowWidth = None
    prevWindowRightIndex = None

    for i, (curTimestamp, curAnomaly) in enumerate(zip(timestamps, anomalyScores)):
      unweightedScore = None
      weightedScore = None

      # If not in a window, check if we've just entered one
      if len(windowLimits) > 0 and curTimestamp == windowLimits[0][0]:
        curWindowLimits = windowLimits.pop(0)
        curWindowName = "%s|%s" % (dataSetName, curWindowLimits[0])
        curWindowRightIndex = timestamps.index(curWindowLimits[1])
        curWindowWidth = float(curWindowRightIndex - timestamps.index(curWindowLimits[0] + 1))

        logger.debug("Entering window: %s (%s)" % (curWindowName, str(curWindowLimits)))

      # If in a window, score as if true positive
      if curWindowLimits is not None:
        # Doesn't the `+ 1` in this equation mean we can _never_ have a positionInWindow == 0?
        positionInWindow = -(curWindowRightIndex - i + 1) / curWindowWidth
        unweightedScore = scaledSigmoid(positionInWindow)
        weightedScore = unweightedScore * self.tpWeight / maxTP  # Why is `maxTP` here?

      # If outside a window, score as if false positive
      else:
        if prevWindowRightIndex is None:
          positionPastWindow = 3.0
        else:
          positionPastWindow = abs(prevWindowRightIndex - i) / float(prevWindowWidth - 1)

        unweightedScore = scaledSigmoid(positionPastWindow)
        weightedScore = unweightedScore * self.fpWeight

      pointWindowName = curWindowName if i >= probationaryLength else "probationary"
      point = AnomalyPoint(curTimestamp, curAnomaly, weightedScore, pointWindowName)

      anomalyList.append(point)

      # If at right-edge of window, exit window.
      # This happens after processing the current point and appending it to the list.
      if curWindowLimits is not None and curTimestamp == curWindowLimits[1]:
        logger.debug("Exiting window: %s" % curWindowName)
        prevWindowRightIndex = i
        prevWindowWidth = curWindowWidth
        curWindowLimits = None
        curWindowName = None
        curWindowWidth = None
        curWindowRightIndex = None

    return anomalyList



  def _optimizeAnomalyDicts(self):
    """Return (threshold, score) with highest score based on sweep score algorithm."""
    pass

  def _scoreAnomalyDicts(self):
    pass

if __name__ == '__main__':
  logging.basicConfig()
  logger.setLevel(logging.DEBUG)
  o = Optimizer()
  print(o)
  c = Corpus('results/numenta')
  print(c)
  print(c.numDataFiles)
  print(c.dataFiles.keys())

  a = AnomalyPoint("jan 1, 2018", 0.4, 1.0, None)
  print(a)