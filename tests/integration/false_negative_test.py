# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import pandas

import unittest2 as unittest
import datetime

from nab.scorer import Scorer
from nab.test_helpers import generateTimestamps, generateWindows, generateLabels



class FalseNegativeTests(unittest.TestCase):


  def test_FalseNegativeCausesNegativeScore(self):
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

    predictions = pandas.Series([0]*length)

    windows = generateWindows(timestamps, numWindows, windowSize)

    labels = generateLabels(timestamps, windows)

    costMatrix = {"tpWeight": 1.0,
                  "fnWeight": 2.0,
                  "fpWeight": 3.0,
                  "tnWeight": 4.0}

    scorer = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)
    (_,score) = scorer.getScore()

    self.assertTrue(abs(score + costMatrix['fnWeight']) < 0.1)

    # Ensure counts are correct.
    self.assertEqual(scorer.counts['tn'], length-windowSize*numWindows)
    self.assertEqual(scorer.counts['tp'], 0)
    self.assertEqual(scorer.counts['fp'], 0)
    self.assertEqual(scorer.counts['fn'], windowSize*numWindows)



  def test_FourFalseNegatives(self):
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
    predictions = pandas.Series([0]*length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)

    costMatrix = {"tpWeight": 1.0,
                  "fnWeight": 2.0,
                  "fpWeight": 3.0,
                  "tnWeight": 4.0}

    scorer = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)
    (_,score) = scorer.getScore()

    self.assertTrue(abs(score + 4*costMatrix['fnWeight']) < 0.01)

    # Ensure counts are correct.
    self.assertEqual(scorer.counts['tn'], length-windowSize*numWindows)
    self.assertEqual(scorer.counts['tp'], 0)
    self.assertEqual(scorer.counts['fp'], 0)
    self.assertEqual(scorer.counts['fn'], windowSize*numWindows)



if __name__ == '__main__':
  unittest.main()
