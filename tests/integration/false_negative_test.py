# Copyright 2014-2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import datetime
import pandas
import unittest

from nab.sweeper import Sweeper
from nab.test_helpers import generateTimestamps, generateWindows



class FalseNegativeTests(unittest.TestCase):

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
  

  def testFalseNegativeCausesNegativeScore(self):
    """
    A false negative with only one window should have exactly the negative
    of the false negative score.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 1000
    numWindows = 1
    windowSize = 10

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    anomalyScores = pandas.Series([0]*length)
    threshold = 1.0

    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    (scores, matchingRow) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )

    self.assertEqual(matchingRow.score, -self.costMatrix["fnWeight"])
    self._checkCounts(matchingRow, length-windowSize*numWindows, 0, 0,
      windowSize*numWindows)


  def testFourFalseNegatives(self):
    """
    A false negative with four windows should have exactly four times
    the negative of the false negative score.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 2000
    numWindows = 4
    windowSize = 10

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    anomalyScores = pandas.Series([0] * length)
    threshold = 1

    sweeper = Sweeper(probationPercent=0, costMatrix=self.costMatrix)
    (scores, matchingRow) = sweeper.scoreDataSet(
      timestamps,
      anomalyScores,
      windows,
      "testData",
      threshold
    )

    self.assertEqual(matchingRow.score, 4 * -self.costMatrix["fnWeight"])
    self._checkCounts(matchingRow, length - windowSize * numWindows, 0, 0,
                      windowSize * numWindows)


if __name__ == '__main__':
  unittest.main()
