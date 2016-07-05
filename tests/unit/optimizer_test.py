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

"""Tests nab.optimizer for finding the local/global maxima of several
functions"""

import datetime
import unittest

import pandas

from nab import corpus, labeler, optimizer, scorer

COST_MATRIX = {
  "tpWeight": 1.0,
  "fnWeight": 1.0,
  "fpWeight": 0.11,
  "tnWeight": 1.0,
}



def _getData1():
  window1 = optimizer._WindowInfo(start=3, end=6, detectedAnomalies=[])
  window2 = optimizer._WindowInfo(start=9, end=11, detectedAnomalies=[])

  return [
    optimizer._DataInfo(anomalyScore=0.0, idx=0, lastWindow=None,
                        probation=True),
    optimizer._DataInfo(anomalyScore=0.2, idx=1, lastWindow=None,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.1, idx=2, lastWindow=None,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.1, idx=3, lastWindow=window1,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.3, idx=4, lastWindow=window1,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.4, idx=5, lastWindow=window1,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.1, idx=6, lastWindow=window1,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.1, idx=7, lastWindow=window1,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.1, idx=8, lastWindow=window1,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.9, idx=9, lastWindow=window2,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.7, idx=10, lastWindow=window2,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.1, idx=11, lastWindow=window2,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.3, idx=12, lastWindow=window2,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.2, idx=13, lastWindow=window2,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.01, idx=14, lastWindow=window2,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.11, idx=15, lastWindow=window2,
                        probation=False),
  ]



def _getData2():
  return [
    optimizer._DataInfo(anomalyScore=0.12, idx=0, lastWindow=None,
                        probation=True),
    optimizer._DataInfo(anomalyScore=0.31, idx=1, lastWindow=None,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.41, idx=2, lastWindow=None,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.21, idx=3, lastWindow=None,
                        probation=False),
  ]



def _getData3():
  window1 = optimizer._WindowInfo(start=1, end=2, detectedAnomalies=[])

  return [
    optimizer._DataInfo(anomalyScore=0.0, idx=0, lastWindow=None,
                        probation=True),
    optimizer._DataInfo(anomalyScore=0.6, idx=1, lastWindow=window1,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.9, idx=2, lastWindow=window1,
                        probation=False),
    optimizer._DataInfo(anomalyScore=0.4, idx=3, lastWindow=window1,
                        probation=False),
  ]



class OptimizerTest(unittest.TestCase):


  def testComputeScoreChangeFalsePositiveNoWindow(self):
    dataInfo = optimizer._DataInfo(idx=1, anomalyScore=0.1, lastWindow=None,
                                   probation=False)
    scoreChange = optimizer._computeScoreChange(dataInfo, COST_MATRIX)
    self.assertAlmostEqual(-COST_MATRIX["fpWeight"], scoreChange[0])
    self.assertSetEqual(set(("tn", "fp")), set(scoreChange[1].keys()))
    self.assertEqual(1, scoreChange[1]["fp"])
    self.assertEqual(-1, scoreChange[1]["tn"])


  def testComputeScoreChangeFalsePositiveWithFarWindow(self):
    windowInfo = optimizer._WindowInfo(start=3, end=5, detectedAnomalies=[])
    dataInfo = optimizer._DataInfo(idx=150, anomalyScore=0.1,
                                   lastWindow=windowInfo, probation=False)
    scoreChange = optimizer._computeScoreChange(dataInfo, COST_MATRIX)
    self.assertAlmostEqual(-COST_MATRIX["fpWeight"], scoreChange[0])
    self.assertSetEqual(set(("tn", "fp")), set(scoreChange[1].keys()))
    self.assertEqual(1, scoreChange[1]["fp"])
    self.assertEqual(-1, scoreChange[1]["tn"])


  def testComputeScoreChangeFalsePositiveWithCloseWindow(self):
    windowInfo = optimizer._WindowInfo(start=3, end=5, detectedAnomalies=[])
    dataInfo = optimizer._DataInfo(idx=6, anomalyScore=0.1,
                                   lastWindow=windowInfo, probation=False)
    scoreChange = optimizer._computeScoreChange(dataInfo, COST_MATRIX)
    self.assertAlmostEqual(-0.8482836399575129 * COST_MATRIX["fpWeight"],
                           scoreChange[0])
    self.assertSetEqual(set(("tn", "fp")), set(scoreChange[1].keys()))
    self.assertEqual(1, scoreChange[1]["fp"])
    self.assertEqual(-1, scoreChange[1]["tn"])


  def testComputeThresholdScoresComplex(self):
    results = optimizer._computeThresholdScores(_getData1(), 2, COST_MATRIX)
    self.assertAlmostEqual(0.3, results[0].threshold)


  def testComputeThresholdScoresNoWindows(self):
    results = optimizer._computeThresholdScores(_getData2(), 0, COST_MATRIX)
    self.assertGreater(results[0].threshold, 1.0)


  def testComputeThresholdScoresCombined(self):
    results = optimizer._computeThresholdScores(_getData1() + _getData2(), 2,
                                                COST_MATRIX)
    self.assertAlmostEqual(0.4, results[0].threshold)


  def testComputeThresholdScoresPerfectDetection(self):
    data = _getData3()
    results = optimizer._computeThresholdScores(data, 1, COST_MATRIX)
    self.assertAlmostEqual(0.6, results[0].threshold)

    for score, threshold, counts in results:
      now = datetime.datetime.now() - datetime.timedelta(hours=1)
      inc = datetime.timedelta(minutes=5)
      # Datetime for each row
      timestamps = [now + (inc * i) for i, _ in enumerate(data)]

      # True iff detector anomaly score is above the threshold
      predictions = pandas.Series(
          [int(d.anomalyScore >= threshold) for d in data])
      # Ground truth: whether each row is in a window
      labels = pandas.DataFrame(
          [0, 1, 1, 0])
      # List of (startDatetime, endDatetime) for each window
      windowLimits = [timestamps[1:3]]

      # Skip scoring the first row
      probationaryPeriod = 1

      actualScore = scorer.Scorer(
          timestamps, predictions, labels, windowLimits, COST_MATRIX,
          probationaryPeriod).getScore()[1]

      self.assertAlmostEqual(actualScore, score)



if __name__ == "__main__":
  unittest.main()
