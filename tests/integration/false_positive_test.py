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

import datetime
import pandas
import unittest

from nab.scorer import Scorer
from nab.test_helpers import generateTimestamps, generateWindows, generateLabels



class FalsePositiveTests(unittest.TestCase):


  def _checkCounts(self, counts, tn, tp, fp, fn):
    """Ensure the metric counts are correct."""
    self.assertEqual(counts['tn'], tn, "Incorrect tn count")
    self.assertEqual(counts['tp'], tp, "Incorrect tp count")
    self.assertEqual(counts['fp'], fp, "Incorrect fp count")
    self.assertEqual(counts['fn'], fn, "Incorrect fn count")
  
  
  def setUp(self):
    self.costMatrix = {"tpWeight": 1.0,
                       "fnWeight": 1.0,
                       "fpWeight": 1.0,
                       "tnWeight": 1.0}


  def testFalsePositiveMeansNegativeScore(self):
    """
    A false positive should make the score negative.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 1000
    numWindows = 1
    windowSize = 10

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)

    predictions[0] = 1
    scorer = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score) = scorer.getScore()
    self.assertTrue(score < 0)
    self._checkCounts(scorer.counts, length-windowSize*numWindows-1, 0, 1,
      windowSize*numWindows)


  def testTwoFalsePositivesIsWorseThanOne(self):
    """
    For two false positives A and B in a file, the score given A and B should be
    more negative than the score given just A.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 1000
    numWindows = 1
    windowSize = 10

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)

    predictions[0] = 1
    scorer1 = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score1) = scorer1.getScore()

    predictions[1] = 1
    scorer2 = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score2) = scorer2.getScore()

    self.assertTrue(score2 < score1)
    self._checkCounts(scorer1.counts, length-windowSize*numWindows-1, 0, 1,
      windowSize*numWindows)
    self._checkCounts(scorer2.counts, length-windowSize*numWindows-2, 0, 2,
      windowSize*numWindows)


  def testOneFalsePositiveNoWindow(self):
    """
    When there is no window (i.e. no anomaly), a false positive should still
    result in a negative score, specifically negative the FP weight.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 1000
    numWindows = 0
    windowSize = 10

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)

    predictions[0] = 1
    scorer = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score) = scorer.getScore()
    
    self.assertTrue(score == -self.costMatrix["fpWeight"])
    self._checkCounts(scorer.counts, length-windowSize*numWindows-1, 0, 1,
      windowSize*numWindows)


  def testEarlierFalsePositiveAfterWindowIsBetter(self):
    """For two false positives A and B, where A occurs earlier than B, the
    score change due to A will be less than the score change due to B.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10
    numWindows = 1
    windowSize = 2

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    predictions1 = pandas.Series([0]*length)
    predictions2 = pandas.Series([0]*length)
    t1, t2 = windows[0]

    index1 = timestamps[timestamps == t2].index[0] + 1
    predictions1[index1] = 1
    scorer1 = Scorer(timestamps, predictions1, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score1) = scorer1.getScore()

    predictions2[index1+1] = 1
    scorer2 = Scorer(timestamps, predictions2, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score2) = scorer2.getScore()

    self.assertTrue(score1 > score2)
    self._checkCounts(scorer1.counts, length-windowSize*numWindows-1, 0, 1,
      windowSize*numWindows)
    self._checkCounts(scorer2.counts, length-windowSize*numWindows-1, 0, 1,
      windowSize*numWindows)


if __name__ == '__main__':
  unittest.main()
