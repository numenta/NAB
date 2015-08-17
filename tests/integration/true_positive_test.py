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



class TruePositiveTest(unittest.TestCase):


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


  def testFirstTruePositiveWithinWindow(self):
    """
    First record within window has a score approximately equal to 
    self.costMatrix["tpWeight"]; within 4 decimal places is more than enough
    precision.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10
    numWindows = 1
    windowSize = 2

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)

    index = timestamps[timestamps == windows[0][0]].index[0]
    predictions[index] = 1
    scorer = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score) = scorer.getScore()

    self.assertAlmostEquals(score, self.costMatrix["tpWeight"], 4)
    self._checkCounts(scorer.counts, length-windowSize*numWindows, 1, 0,
      windowSize*numWindows-1)


  def testEarlierTruePositiveIsBetter(self):
    """
    If two algorithms both get a true positive within a window, the algorithm
    with the earlier true positive (in the window) should get a higher score.
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

    index1 = timestamps[timestamps == t1].index[0]
    predictions1[index1] = 1
    scorer1 = Scorer(timestamps, predictions1, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score1) = scorer1.getScore()

    index2 = timestamps[timestamps == t2].index[0]
    predictions2[index2] = 1
    scorer2 = Scorer(timestamps, predictions2, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score2) = scorer2.getScore()

    self.assertTrue(score1 > score2, "The earlier TP score is not greater than "
      "the later TP. They are %f and %f, respectively." % (score1, score2))
    self._checkCounts(scorer1.counts, length-windowSize*numWindows, 1, 0,
      windowSize*numWindows-1)
    self._checkCounts(scorer2.counts, length-windowSize*numWindows, 1, 0,
      windowSize*numWindows-1)


  def testOnlyScoreFirstTruePositiveWithinWindow(self):
    """
    An algorithm making multiple detections within a window (i.e. true positive)
    should only be scored for the earliest true positive.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10
    numWindows = 1
    windowSize = 2

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)
    window = windows[0]
    t1, t2 = window

    index1 = timestamps[timestamps == t1].index[0]
    predictions[index1] = 1
    scorer1 = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score1) = scorer1.getScore()

    index2 = timestamps[timestamps == t2].index[0]
    predictions[index2] = 1
    scorer2 = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score2) = scorer2.getScore()

    self.assertEqual(score1, score2)
    self._checkCounts(scorer1.counts, length-windowSize*numWindows, 1, 0,
      windowSize*numWindows-1)
    self._checkCounts(scorer2.counts, length-windowSize*numWindows, 2, 0,
      windowSize*numWindows-2)


  def testTruePositivesWithDifferentWindowSizes(self):
    """
    True positives  at the left edge of windows should have the same score
    regardless of width of window.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10
    numWindows = 1
    timestamps = generateTimestamps(start, increment, length)
    
    windowSize1 = 2
    windows1 = generateWindows(timestamps, numWindows, windowSize1)
    labels1 = generateLabels(timestamps, windows1)
    index = timestamps[timestamps == windows1[0][0]].index[0]
    predictions1 = pandas.Series([0]*length)
    predictions1[index] = 1
    
    windowSize2 = 3
    windows2 = generateWindows(timestamps, numWindows, windowSize2)
    labels2 = generateLabels(timestamps, windows2)
    index = timestamps[timestamps == windows2[0][0]].index[0]
    predictions2 = pandas.Series([0]*length)
    predictions2[index] = 1

    scorer1 = Scorer(timestamps, predictions1, labels1, windows1,
      self.costMatrix, probationaryPeriod=0)
    (_, score1) = scorer1.getScore()
    scorer2 = Scorer(timestamps, predictions2, labels2, windows2,
      self.costMatrix, probationaryPeriod=0)
    (_, score2) = scorer2.getScore()
    
    self.assertEqual(score1, score2)
    self._checkCounts(scorer1.counts, length-windowSize1*numWindows, 1, 0,
      windowSize1*numWindows-1)
    self._checkCounts(scorer2.counts, length-windowSize2*numWindows, 1, 0,
      windowSize2*numWindows-1)


  def testTruePositiveAtRightEdgeOfWindow(self):
    """
    True positives at the right edge of a window should yield a score of
    approximately zero; the scaled sigmoid scoring function crosses the zero
    between a given window's last timestamp and the next timestamp (immediately
    following the window.
    """
    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 1000
    numWindows = 1
    windowSize = 100

    timestamps = generateTimestamps(start, increment, length)
    windows = generateWindows(timestamps, numWindows, windowSize)
    labels = generateLabels(timestamps, windows)
    predictions = pandas.Series([0]*length)

    # Make prediction at end of the window; TP
    index = timestamps[timestamps == windows[0][1]].index[0]
    predictions[index] = 1
    scorer1 = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score1) = scorer1.getScore()
    # Make prediction just after the window; FP
    predictions[index] = 0
    index += 1
    predictions[index] = 1
    scorer2 = Scorer(timestamps, predictions, labels, windows, self.costMatrix,
      probationaryPeriod=0)
    (_, score2) = scorer2.getScore()

    # TP score + FP score + 1 should be very close to 0; the 1 is added to
    # account for the subsequent FN contribution.
    self.assertAlmostEquals(score1 + score2 + 1, 0.0, 3)
    self._checkCounts(scorer1.counts, length-windowSize*numWindows, 1, 0,
      windowSize*numWindows-1)
    self._checkCounts(scorer2.counts, length-windowSize*numWindows-1, 0, 1,
      windowSize*numWindows)


if __name__ == '__main__':
  unittest.main()
