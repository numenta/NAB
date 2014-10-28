 # ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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


class TruePositiveTest(unittest.TestCase):

  def _checkCounts(self, counts, tn, tp, fp, fn):
    """Assert that the counts matrix has the specified values."""
    self.assertEqual(counts['tn'], tn, "Incorrect tn count")
    self.assertEqual(counts['tp'], tp, "Incorrect tp count")
    self.assertEqual(counts['fp'], fp, "Incorrect fp count")
    self.assertEqual(counts['fn'], fn, "Incorrect fn count")


  def test_nullCase(self):
    """No windows and no predictions means that the score should be 0."""

    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10

    timestamps = generateTimestamps(start, increment, length)
    predictions = pandas.Series([0]*length)
    labels = pandas.Series([0]*length)
    windows = []

    costMatrix = {"tpWeight": 1.0,
                  "fnWeight": 2.0,
                  "fpWeight": 3.0,
                  "tnWeight": 4.0}

    scorer = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)

    self.assertEqual(scorer.getScore(), 0.0)
    self._checkCounts(scorer.counts, 10, 0, 0, 0)


#  @unittest.skip("Not working yet")
  def test_firstTruePositiveWithinWindow(self):
    """
    First record within window has a score close to costMatrix["tpWeight"].
    Since we use Sigmoids, it will never be exactly 1.
    """

    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10
    numWindows = 1
    windowSize = 2

    timestamps = generateTimestamps(start, increment, length)
    predictions = pandas.Series([0]*length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)

    costMatrix = {"tpWeight": 1.0,
                  "fnWeight": 2.0,
                  "fpWeight": 3.0,
                  "tnWeight": 4.0}

    index = timestamps[timestamps == windows[0][0]].index[0]
    predictions[index] = 1
    print "left edge of window=",windows[0][0]
    print "index=",index
    print "prediction=\n",predictions

    scorer = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)

    print "score=",scorer.getScore()

    self.assertTrue(costMatrix["tpWeight"] - scorer.getScore() <= 1)


  def test_earlierTruePositiveIsBetter(self):
    """
    If two algorithms both get a true positive within a window, the algorithm
    that labeled a true positive earlier in the window will get a higher score.
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
                  "fnWeight": 2.0,
                  "fpWeight": 3.0,
                  "tnWeight": 4.0}

    index1 = timestamps[timestamps == t1].index[0]
    predictions1[index1] = 1

    scorer1 = Scorer(timestamps, predictions1, labels, windows, costMatrix,
      probationaryPeriod=0)
    score1 = scorer1.getScore()

    index2 = timestamps[timestamps == t2].index[0]
    predictions2[index2] = 1

    scorer2 = Scorer(timestamps, predictions2, labels, windows, costMatrix,
      probationaryPeriod=0)
    score2 = scorer2.getScore()

    self.assertTrue(score1 > score2)


  def test_secondTruePositiveWithinWindowIsIgnored(self):
    """
    If there are two true positives within the same window, then the score
    should be only decided by whichever true positive occurred earlier.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10
    numWindows = 1
    windowSize = 2

    timestamps = generateTimestamps(start, increment, length)

    predictions = pandas.Series([0]*length)

    windows = generateWindows(timestamps, numWindows, windowSize)

    labels = generateLabels(timestamps, windows)
    window = windows[0]
    t1, t2 = window

    costMatrix = {"tpWeight": 1.0,
                  "fnWeight": 2.0,
                  "fpWeight": 3.0,
                  "tnWeight": 4.0}

    index1 = timestamps[timestamps == t1].index[0]
    predictions[index1] = 1

    scorer1 = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)

    score1 = scorer1.getScore()

    index2 = timestamps[timestamps == t2].index[0]
    predictions[index2] = 1

    scorer2 = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod=0)

    score2 = scorer2.getScore()

    self.assertEqual(score1, score2)


  @unittest.skip("Not implemented")
  def test_truePositivesWithDifferentWindowSizes(self):
    """
    True positives at the left edge of windows should have the same score
    regardless of width of window.
    """
    pass


  @unittest.skip("Not implemented")
  def test_truePositiveAtRightEdgeOfWindow(self):
    """
    True positive at the right edge of a window should have a score that
    is zero.
    """
    pass

if __name__ == '__main__':
  unittest.main()

