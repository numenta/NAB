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
