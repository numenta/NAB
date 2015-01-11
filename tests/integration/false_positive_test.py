# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
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

class FalsePositiveTests(unittest.TestCase):


  def test_falsePositiveMeansNegativeScore(self):
    """
    A false positive should make the score negative.
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
    "fnWeight": 1.0,
    "fpWeight": 1.0,
    "tnWeight": 1.0}

    predictions[0] = 1

    scorer = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)
    (_, score) = scorer.getScore()

    self.assertTrue(score < 0)

    # Ensure counts are correct.
    self.assertEqual(scorer.counts['tn'], length-windowSize*numWindows-1)
    self.assertEqual(scorer.counts['tp'], 0)
    self.assertEqual(scorer.counts['fp'], 1)
    self.assertEqual(scorer.counts['fn'], windowSize*numWindows)


  def test_twoFalsePositivesIsWorseThanOne(self):
    """False positives have an additive effect on the score. If there are two
    false positives, A and B, in a file, then the score given A and B should be
    larger than the score given just A.
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
    "fnWeight": 1.0,
    "fpWeight": 1.0,
    "tnWeight": 1.0}

    predictions[0] = 1

    scorer1 = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)

    (_, score1) = scorer1.getScore()


    predictions[1] = 1

    scorer2 = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)

    (_, score2) = scorer2.getScore()

    self.assertTrue(score1 > score2)

    # Ensure counts are correct.
    self.assertEqual(scorer1.counts['tn'], length-windowSize*numWindows-1)
    self.assertEqual(scorer1.counts['tp'], 0)
    self.assertEqual(scorer1.counts['fp'], 1)
    self.assertEqual(scorer1.counts['fn'], windowSize*numWindows)

    self.assertEqual(scorer2.counts['tn'], length-windowSize*numWindows-2)
    self.assertEqual(scorer2.counts['tp'], 0)
    self.assertEqual(scorer2.counts['fp'], 2)
    self.assertEqual(scorer2.counts['fn'], windowSize*numWindows)


  def test_oneFalsePositiveNoWindow(self):
    """
    When there is no window (meaning no anomaly), a false positive should still
    result in a negative score.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 1000
    numWindows = 0
    windowSize = 10

    timestamps = generateTimestamps(start, increment, length)

    predictions = pandas.Series([0]*length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)

    costMatrix = {"tpWeight": 1.0,
    "fnWeight": 1.0,
    "fpWeight": 1.0,
    "tnWeight": 1.0}

    predictions[0] = 1

    scorer = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)
    (_, score) = scorer.getScore()

    self.assertTrue(score == -costMatrix["fpWeight"])

    # Ensure counts are correct.
    self.assertEqual(scorer.counts['tn'], length-windowSize*numWindows-1)
    self.assertEqual(scorer.counts['tp'], 0)
    self.assertEqual(scorer.counts['fp'], 1)
    self.assertEqual(scorer.counts['fn'], windowSize*numWindows)


  def test_earlierFalsePositiveAfterWindowIsBetter(self):
    """Imagine there are two false positives A and B that both occur right after
    a window. If A occurs earlier than B, then the score change due to A will be
    less than the score change due to B.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10
    numWindows = 1
    windowSize = 2

    timestamps = generateTimestamps(start, increment, length)

    predictions1 = pandas.Series([0]*length)
    predictions2 = pandas.Series([0]*length)

    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)

    window = windows[0]
    t1, t2 = window

    costMatrix = {"tpWeight": 1.0,
                  "fnWeight": 1.0,
                  "fpWeight": 1.0,
                  "tnWeight": 1.0}

    index1 = timestamps[timestamps == t2].index[0] + 1
    predictions1[index1] = 1

    scorer1 = Scorer(timestamps, predictions1, labels, windows, costMatrix,
      probationaryPeriod=0)
    (_, score1) = scorer1.getScore()

    predictions2[index1+1] = 1

    scorer2 = Scorer(timestamps, predictions2, labels, windows, costMatrix,
      probationaryPeriod=0)
    (_, score2) = scorer2.getScore()

    self.assertTrue(score1 > score2)

    # Ensure counts are correct.
    self.assertEqual(scorer1.counts['tn'], length-windowSize*numWindows-1)
    self.assertEqual(scorer1.counts['tp'], 0)
    self.assertEqual(scorer1.counts['fp'], 1)
    self.assertEqual(scorer1.counts['fn'], windowSize*numWindows)

    self.assertEqual(scorer2.counts['tn'], length-windowSize*numWindows-1)
    self.assertEqual(scorer2.counts['tp'], 0)
    self.assertEqual(scorer2.counts['fp'], 1)
    self.assertEqual(scorer2.counts['fn'], windowSize*numWindows)


if __name__ == '__main__':
  unittest.main()
