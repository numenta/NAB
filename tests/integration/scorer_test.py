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

from nab.scorer import Scorer
from nab.test_helpers import generateTimestamps, generateWindows, generateLabels



class ScorerTest(unittest.TestCase):


  def _checkCounts(self, counts, tn, tp, fp, fn):
    """Ensure the metric counts are correct."""
    self.assertEqual(counts['tn'], tn, "Incorrect tn count")
    self.assertEqual(counts['tp'], tp, "Incorrect tp count")
    self.assertEqual(counts['fp'], fp, "Incorrect fp count")
    self.assertEqual(counts['fn'], fn, "Incorrect fn count")


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

    timestamps = generateTimestamps(start, increment, length)
    predictions = pandas.Series([0]*length)
    labels = pandas.Series([0]*length)
    windows = []

    scorer = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score) = scorer.getScore()

    self.assertEqual(score, 0.0)
    self._checkCounts(scorer.counts, 10, 0, 0, 0)


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
    
    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    
    # Scale for 10% = windowSize/length
    self.costMatrix["fpWeight"] = 0.11
    
    # Make arbitrary detections, score, repeat
    scores = []
    for _ in xrange(20):
      predictions = pandas.Series([0]*length)
      indices = random.sample(range(length), 10)
      predictions[indices] = 1
      scorer = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
        probationaryPeriod=0)
      (_, score) = scorer.getScore()
      scores.append(score)
  
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
    
    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)
    
    costMatrixFN = copy.deepcopy(self.costMatrix)
    costMatrixFN["fnWeight"] = 2.0
    costMatrixFN["fpWeight"] = 0.055
    
    scorer1 = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score1) = scorer1.getScore()
    scorer2 = Scorer(timestamps, predictions, labels, windows, costMatrixFN,
      probationaryPeriod=0)
    (_, score2) = scorer2.getScore()

    self.assertEqual(score1, 0.5*score2)
    self._checkCounts(scorer1.counts, length-windowSize*numWindows, 0, 0,
      windowSize*numWindows)
    self._checkCounts(scorer2.counts, length-windowSize*numWindows, 0, 0,
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
    
    timestamps = generateTimestamps(start, increment, length)
    windows = []
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)
    
    costMatrixFP = copy.deepcopy(self.costMatrix)
    costMatrixFP["fpWeight"] = 2.0
    costMatrixFP["fnWeight"] = 0.5
    # FP
    predictions[0] = 1

    scorer1 = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score1) = scorer1.getScore()
    scorer2 = Scorer(timestamps, predictions, labels, windows, costMatrixFP,
      probationaryPeriod=0)
    (_, score2) = scorer2.getScore()
    
    self.assertEqual(score1, 0.5*score2)
    self._checkCounts(scorer1.counts, length-windowSize*numWindows-1, 0, 1, 0)
    self._checkCounts(scorer2.counts, length-windowSize*numWindows-1, 0, 1, 0)


  def testScoringAllMetrics(self):
    """
    This tests an example set of detections, where all metrics have counts > 0.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 100
    numWindows = 2
    windowSize = 5
    
    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)
    
    index = timestamps[timestamps == windows[0][0]].index[0]
    # TP, add'l TP, and FP
    predictions[index] = 1
    predictions[index+1] = 1
    predictions[index+7] = 1
    
    scorer = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score) = scorer.getScore()
    
    self.assertAlmostEquals(score, -0.9540, 4)
    self._checkCounts(scorer.counts, length-windowSize*numWindows-1, 2, 1, 8)


if __name__ == '__main__':
  unittest.main()
