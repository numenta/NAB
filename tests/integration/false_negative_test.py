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



class FalseNegativeTests(unittest.TestCase):


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
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)

    scorer = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score) = scorer.getScore()

    self.assertTrue(abs(score + self.costMatrix['fnWeight']) < 0.1)
    self._checkCounts(scorer.counts, length-windowSize*numWindows, 0, 0,
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
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)

    scorer = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score) = scorer.getScore()

    self.assertTrue(abs(score + 4*self.costMatrix['fnWeight']) < 0.01)
    self._checkCounts(scorer.counts, length-windowSize*numWindows, 0, 0,
      windowSize*numWindows)


if __name__ == '__main__':
  unittest.main()
