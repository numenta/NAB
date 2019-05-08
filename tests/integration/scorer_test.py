 # ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
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

import copy
import datetime
import pandas
import random
import unittest

from nab.sweeper import Sweeper
from nab.test_helpers import generateTimestamps, generateWindows



class ScorerTest(unittest.TestCase):


  def _checkCounts(self, scoreRow, tn, tp, fp, fn):
    """Ensure the metric counts are correct."""
    self.assertEqual(scoreRow.tn, tn, "Incorrect tn count")
    self.assertEqual(scoreRow.tp, tp, "Incorrect tp count")
    self.assertEqual(scoreRow.fp, fp, "Incorrect fp count")
    self.assertEqual(scoreRow.fn, fn, "Incorrect fn count")


  def setUp(self):
    # Standard application profile
    self.costMatrix = {"tpWeight": 1.0,
                       "fnWeight": 1.0,
                       "fpWeight": 1.0,
                       "tnWeight": 1.0}


  def testNullCase(self):
    """No windows and no predictions should yield a score of 0.0."""
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10
    threshold = 0.5

    timestamps = generateTimestamps(start, increment, length)
    anomalyScores = pandas.Series([0]*length)
    windows = []

    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    (scores, matchingRow) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )

    self.assertEqual(matchingRow.score, 0.0)
    self._checkCounts(matchingRow, 10, 0, 0, 0)


  def testFalsePositiveScaling(self):
    """
    Test scaling the weight of false positives results in an approximate
    balance with the true positives.
    
    The contributions of TP and FP scores should approximately cancel; i.e.
    total score =0. With x windows, this total score should on average decrease
    x/2 because of x FNs. Thus, the acceptable range for score should be
    centered about -x/2.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 100
    numWindows = 1
    windowSize = 10
    threshold = 0.5
    
    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    
    # Scale for 10% = windowSize/length
    self.costMatrix["fpWeight"] = 0.11
    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)

    # Make arbitrary detections, score, repeat
    scores = []
    for _ in range(20):
      anomalyScores = pandas.Series([0]*length)
      indices = random.sample(list(range(length)), 10)
      anomalyScores[indices] = 1
      (scores, matchingRow) = sweeper.scoreDataSet(
        timestamps,
        anomalyScores,
        windows,
        "testData",
        threshold
      )
      scores.append(matchingRow.score)
  
    avgScore = sum(scores)/float(len(scores))

    self.assertTrue(-1.5 <= avgScore <= 0.5, "The average score across 20 sets "
      "of random detections is %f, which is not within the acceptable range "
      "-1.5 to 0.5." % avgScore)
  

  def testRewardLowFalseNegatives(self):
    """
    Given false negatives in the set of detections, the score output with the
    Reward Low False Negatives application profile will be greater than with
    the Standard application profile.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 100
    numWindows = 1
    windowSize = 10
    threshold = 0.5

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    anomalyScores = pandas.Series([0]*length)
    
    costMatrixFN = copy.deepcopy(self.costMatrix)
    costMatrixFN["fnWeight"] = 2.0
    costMatrixFN["fpWeight"] = 0.055

    sweeper1 = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    sweeper2 = Sweeper(probationPercent=0, costMatrix=costMatrixFN)

    (scores, matchingRow1) = sweeper1.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )

    (scores, matchingRow2) = sweeper2.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )


    self.assertEqual(matchingRow1.score, 0.5*matchingRow2.score)
    self._checkCounts(matchingRow1, length-windowSize*numWindows, 0, 0,
      windowSize*numWindows)
    self._checkCounts(matchingRow2, length-windowSize*numWindows, 0, 0,
      windowSize*numWindows)


  def testRewardLowFalsePositives(self):
    """
    Given false positives in the set of detections, the score output with the
    Reward Low False Positives application profile will be greater than with
    the Standard application profile.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 100
    numWindows = 0
    windowSize = 10
    threshold = 0.5
    
    timestamps = generateTimestamps(start, increment, length)
    windows = []
    anomalyScores = pandas.Series([0]*length)
    
    costMatrixFP = copy.deepcopy(self.costMatrix)
    costMatrixFP["fpWeight"] = 2.0
    costMatrixFP["fnWeight"] = 0.5
    # FP
    anomalyScores[0] = 1

    sweeper1 = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    sweeper2 = Sweeper(probationPercent=0, costMatrix=costMatrixFP)

    (scores, matchingRow1) = sweeper1.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )

    (scores, matchingRow2) = sweeper2.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )
    
    self.assertEqual(matchingRow1.score, 0.5*matchingRow2.score)
    self._checkCounts(matchingRow1, length-windowSize*numWindows-1, 0, 1, 0)
    self._checkCounts(matchingRow2, length-windowSize*numWindows-1, 0, 1, 0)


  def testScoringAllMetrics(self):
    """
    This tests an example set of detections, where all metrics have counts > 0.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 100
    numWindows = 2
    windowSize = 5
    threshold = 0.5
    
    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    anomalyScores = pandas.Series([0]*length)
    
    index = timestamps[timestamps == windows[0][0]].index[0]
    # TP, add'l TP, and FP
    anomalyScores[index] = 1
    anomalyScores[index+1] = 1
    anomalyScores[index+7] = 1

    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)

    (scores, matchingRow) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )
    
    self.assertAlmostEqual(matchingRow.score, -0.9540, 4)
    self._checkCounts(matchingRow, length-windowSize*numWindows-1, 2, 1, 8)


if __name__ == '__main__':
  unittest.main()
