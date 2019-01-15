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

from nab.sweeper import Sweeper
from nab.test_helpers import generateTimestamps, generateWindows



class FalsePositiveTests(unittest.TestCase):


  def _checkCounts(self, scoreRow, tn, tp, fp, fn):
    """Ensure the metric counts are correct."""
    self.assertEqual(scoreRow.tn, tn, "Incorrect tn count")
    self.assertEqual(scoreRow.tp, tp, "Incorrect tp count")
    self.assertEqual(scoreRow.fp, fp, "Incorrect fp count")
    self.assertEqual(scoreRow.fn, fn, "Incorrect fn count")
  
  
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
    threshold = 0.5

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    anomalyScores = pandas.Series([0]*length)

    anomalyScores[0] = 1
    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    (scores, matchingRow) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )
    self.assertTrue(matchingRow.score < 0)
    self._checkCounts(matchingRow, length-windowSize*numWindows-1, 0, 1,
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
    threshold = 0.5

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    anomalyScores = pandas.Series([0]*length)

    anomalyScores[0] = 1
    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    (scores, matchingRow1) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )

    anomalyScores[1] = 1
    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    (scores, matchingRow2) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )

    self.assertTrue(matchingRow2.score < matchingRow1.score)
    self._checkCounts(matchingRow1, length-windowSize*numWindows-1, 0, 1,
      windowSize*numWindows)
    self._checkCounts(matchingRow2, length-windowSize*numWindows-2, 0, 2,
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
    threshold = 0.5

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    anomalyScores = pandas.Series([0]*length)

    anomalyScores[0] = 1
    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    (scores, matchingRow) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )
    
    self.assertEqual(matchingRow.score, -self.costMatrix["fpWeight"])
    self._checkCounts(matchingRow, length-windowSize*numWindows-1, 0, 1,
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
    threshold = 0.5

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    anomalyScores1 = pandas.Series([0]*length)
    anomalyScores2 = pandas.Series([0]*length)
    t1, t2 = windows[0]

    index1 = timestamps[timestamps == t2].index[0] + 1
    anomalyScores1[index1] = 1
    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    (scores, matchingRow1) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores1,
      windows,
      "testData",
      threshold
    )

    anomalyScores2[index1+1] = 1
    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    (scores, matchingRow2) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores2,
      windows,
      "testData",
      threshold
    )

    self.assertTrue(matchingRow1.score > matchingRow2.score)
    self._checkCounts(matchingRow1, length-windowSize*numWindows-1, 0, 1,
      windowSize*numWindows)
    self._checkCounts(matchingRow2, length-windowSize*numWindows-1, 0, 1,
      windowSize*numWindows)


if __name__ == '__main__':
  unittest.main()
