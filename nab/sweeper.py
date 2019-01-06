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

logger = logging.getLogger(__name__)
AnomalyPoint = namedtuple("AnomalyPoint", ["timestamp", "anomalyScore", "sweepScore", "windowName"])
ThresholdScore = namedtuple("ThresholdScore", ["threshold", "score", "tp", "tn", "fp", "fn", "total"])


def sigmoid(x):
  """Standard sigmoid function."""
  return 1 / (1 + math.exp(-x))


def scaledSigmoid(relativePositionInWindow):
  """Return a scaled sigmoid function given a relative position within a
  labeled window.  The function is computed as follows:

  A relative position of -1.0 is the far left edge of the anomaly window and
  corresponds to S = 2*sigmoid(5) - 1.0 = 0.98661.  This is the earliest to be
  counted as a true positive.

  A relative position of -0.5 is halfway into the anomaly window and
  corresponds to S = 2*sigmoid(0.5*5) - 1.0 = 0.84828.

  A relative position of 0.0 consists of the right edge of the window and
  corresponds to S = 2*sigmoid(0) - 1 = 0.0.

  Relative positions > 0 correspond to false positives increasingly far away
  from the right edge of the window. A relative position of 1.0 is past the
  right  edge of the  window and corresponds to a score of 2*sigmoid(-5) - 1.0 =
  -0.98661.

  @param  relativePositionInWindow (float)  A relative position
                                            within a window calculated per the
                                            rules above.

  @return (float)
  """
  if relativePositionInWindow >= 3.0:
    # FP well behind window
    return -1.0
  else:
    return 2*sigmoid(-5*relativePositionInWindow) - 1.0



class Sweeper(object):


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


  def _getProbationaryLength(self, numRows):
    return min(math.floor(self.probationPercent * numRows), self.probationPercent * 5000)


  def _prepAnomalyListForScoring(self, inputAnomalyList):
    """Sort by anomaly score and filter all rows with 'probationary' window name"""
    return sorted(
      [x for x in inputAnomalyList if x.windowName != 'probationary'],
      key=lambda x: x.anomalyScore,
      reverse=True)


  def _prepareScoreByThresholdParts(self, inputAnomalyList):
    scoreParts = {"fp": 0}
    for row in inputAnomalyList:
      if row.windowName not in ('probationary', None):
        scoreParts[row.windowName] = -self.fnWeight
    return scoreParts


  def calcSweepScore(self, timestamps, anomalyScores, windowLimits, dataSetName):
    assert len(timestamps) == len(anomalyScores), "timestamps and anomalyScores should not be different lengths!"
    timestamps = list(timestamps)
    windowLimits = list(windowLimits)  # Copy because we mutate this list
    # The final list of anomaly points returned from this function.
    # Used for threshold optimization and scoring in other functions.
    anomalyList = []

    # One-time config variables
    maxTP = scaledSigmoid(-1.0)
    probationaryLength = self._getProbationaryLength(len(timestamps))

    # Iteration variables - these update as we iterate through the data
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
        curWindowWidth = float(curWindowRightIndex - timestamps.index(curWindowLimits[0]) + 1)

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


  def calcScoreByThreshold(self, anomalyList):
    scorableList = self._prepAnomalyListForScoring(anomalyList)
    scoreParts = self._prepareScoreByThresholdParts(scorableList)
    scoresByThreshold = []  # The final list we return
    curThreshold = 1.1  # Start threshold eliminates all rows --> full false negative score

    # Initialize counts:
    # * every point in a window is a false negative
    # * every point outside a window is a false positive
    tn = sum(1 if x.windowName is None else 0 for x in scorableList)
    fn = sum(1 if x.windowName is not None else 0 for x in scorableList)
    tp = 0
    fp = 0

    # Iterate through every data point, starting with highest anomaly scores and working down.
    # Whenever we reach a new anomaly score, we save the current score and begin calculating
    # the score for the new, lower threshold. Every data point we iterate over is 'active'
    # for the current threshold level, so the point is either a true positive (has a `windowName`)
    # or a false positive (`windowName is None`).
    for dataPoint in scorableList:
      # Check if we've reached a new threshold
      if dataPoint.anomalyScore != curThreshold:
        curScore = sum(scoreParts.values())
        s = ThresholdScore(curThreshold, curScore, tp, tn, fp, fn, tp + tn + fp + fn)
        scoresByThreshold.append(s)
        curThreshold = dataPoint.anomalyScore

      # Adjust counts
      if dataPoint.windowName is not None:
        tp += 1
        fn -= 1
      else:
        fp += 1
        tn -= 1

      if dataPoint.windowName is None:
        scoreParts["fp"] += dataPoint.sweepScore
      else:
        scoreParts[dataPoint.windowName] = max(scoreParts[dataPoint.windowName], dataPoint.sweepScore)
    else:
      # Make sure to save the score for the last threshold
      curScore = sum(scoreParts.values())
      s = ThresholdScore(curThreshold, curScore, tp, tn, fp, fn, tp + tn + fp + fn)
      scoresByThreshold.append(s)

    return scoresByThreshold


  def scoreDataSet(self, timestamps, anomalyScores, windowLimits, dataSetName, threshold):
    anomalyList = self.calcSweepScore(timestamps, anomalyScores, windowLimits, dataSetName)
    scoresByThreshold = self.calcScoreByThreshold(anomalyList)

    matchingRow = None
    prevRow = None
    for thresholdScore in scoresByThreshold:
      if thresholdScore.threshold == threshold:
        matchingRow = thresholdScore
        break
      elif thresholdScore.threshold < threshold:
        matchingRow = prevRow
        break

      prevRow = thresholdScore

    return (
      [x.sweepScore for x in anomalyList],  # Return sweepScore for each row, to be added to score file
      matchingRow
    )
