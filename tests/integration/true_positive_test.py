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

from nab.scorer import Scorer, scoreCorpus
import pandas

import unittest2 as unittest
import datetime



def generateTimestamps(start, increment, length):
  timestamps = pandas.Series([start])
  for i in xrange(length - 1):
    timestamps.loc[i + 1] = timestamps.loc[i] + increment
  return timestamps


def generateWindows(timestamps, numWindows, windowSize):
  start = timestamps[0]
  delta = timestamps[1] - timestamps[0]
  length = len(timestamps)
  diff = int(round((length - numWindows * windowSize) / float(numWindows + 1)))
  windows = []
  for i in xrange(numWindows):
    t1 = start + delta * diff * (i + 1) + (delta * windowSize * i)
    t2 = t1 + (delta) * (windowSize - 1)
    if not any(timestamps == t1) or not any(timestamps == t2):
      raise ValueError("You got the wrong times from the window generator")
    windows.append([t1, t2])
  return windows


def generateLabels(timestamps, windows):
  labels = pandas.Series([0]*len(timestamps))
  for t1, t2 in windows:
    subset = timestamps[timestamps >= t1][timestamps <= t2]
    indices = subset.loc[:].index
    labels.values[indices] = 1
  return labels


class TruePositiveTest(unittest.TestCase):

  def test_nullCase(self):
    """No windows and no predictions means that the score should be 0.
    """

    start = datetime.datetime.now()
    increment = datetime.timedelta(minutes=5)
    length = 10
    numWindows = 0
    windowSize = 0

    timestamps = generateTimestamps(start, increment, length)

    predictions = pandas.Series([0]*length)

    labels = pandas.Series([0]*length)

    windows = []

    costMatrix = {"tpWeight": 1.0,
    "fnWeight": 2.0,
    "fpWeight": 3.0,
    "tnWeight": 4.0}

    probationaryPeriod = 0

    scorer = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod)

    self.assertEqual(scorer.getScore(), 0.0)


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

    probationaryPeriod = 0

    predictions[timestamps[timestamps == windows[0][0]]].values[0] = 1

    scorer = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod)

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

    probationaryPeriod = 0

    index1 = timestamps[timestamps == t1].index[0]
    predictions1[index1] = 1

    scorer1 = Scorer(timestamps, predictions1, labels, windows, costMatrix,
      probationaryPeriod)

    index2 = timestamps[timestamps == t2].index[0]
    predictions2[index2] = 1

    scorer2 = Scorer(timestamps, predictions2, labels, windows, costMatrix,
      probationaryPeriod)

    self.assertTrue(scorer1.getScore() > scorer2.getScore())


  def test_secondTruePositiveWithinWindowIsIgnored(self):
    """If there are two true positives within the same window, then the score
    should be only decided by whichever true positive occured earlier.
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

    probationaryPeriod = 0

    index1 = timestamps[timestamps == t1].index[0]
    predictions[index1] = 1

    scorer1 = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod)

    score1 = scorer1.getScore()

    index2 = timestamps[timestamps == t2].index[0]
    predictions[index2] = 1

    scorer2 = Scorer(timestamps, predictions, labels, windows, costMatrix,
      probationaryPeriod)

    score2 = scorer2.getScore()

    self.assertEqual(score1, score2)


if __name__ == '__main__':
  unittest.main()

