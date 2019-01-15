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
import pytest

from nab.sweeper import (
  AnomalyPoint,
  Sweeper,
  ThresholdScore,
  prepAnomalyListForScoring
)


class TestSweeper(object):
  def testOptimizerInit(self):
    o = Sweeper()
    assert o.probationPercent is not None

    o = Sweeper(probationPercent=0.30)
    assert o.probationPercent == 0.30

    o = Sweeper(costMatrix={"tpWeight": 0, "fpWeight": 1, "fnWeight": 2})
    assert o.tpWeight == 0
    assert o.fpWeight == 1
    assert o.fnWeight == 2

  @pytest.mark.parametrize("numRows,probationaryPercent,expectedLength", [
    (100, 0.0, 0),  # 0% probationary --> length 0
    (100, 1.0, 100),  # 100% --> length 100
    (100, 0.1, 10),
    (100, 0.15, 15),
    (5000, 0.1, 500),
    (6000, 0.1, 500),  # Cap at 5000 works as expected
  ])
  def testGetProbationaryLength(self, numRows, probationaryPercent, expectedLength):
    o = Sweeper(probationPercent=probationaryPercent)
    actualLength = o._getProbationaryLength(numRows)
    assert actualLength == expectedLength

  def testSetCostMatrix(self):
    o = Sweeper()
    assert o.tpWeight == 0
    assert o.fpWeight == 0
    assert o.fnWeight == 0

    # These are all arbitrary.
    expectedTP = 2.0
    expectedFN = 3.0
    expectedFP = 4.0

    costMatrix = {
      "tpWeight": expectedTP,
      "fnWeight": expectedFN,
      "fpWeight": expectedFP
    }

    o.setCostMatrix(costMatrix)

    assert o.tpWeight == expectedTP
    assert o.fnWeight == expectedFN
    assert o.fpWeight == expectedFP

  def testCalcSweepScoreWindowScoreInteraction(self):
    """Scores inside a window should be positive; all others should be negative."""
    numRows = 100
    fakeAnomalyScores = [1 for _ in range(numRows)]
    fakeTimestamps = [i for i in range(numRows)]  # We'll use numbers, even though real data uses dates
    fakeName = "TestDataSet"

    windowA = (30, 39)
    windowB = (75, 95)
    windowLimits = [windowA, windowB]
    expectedInWindowCount = (windowA[1] - windowA[0] + 1) + (windowB[1] - windowB[0] + 1)

    # Standard profile
    costMatrix = {
      "tpWeight": 1.0,
      "fnWeight": 1.0,
      "fpWeight": 0.11,
    }
    probationPercent = 0.1
    o = Sweeper(probationPercent=probationPercent, costMatrix=costMatrix)
    scoredAnomalies = o.calcSweepScore(fakeTimestamps, fakeAnomalyScores, windowLimits, fakeName)

    # Check that correct number of AnomalyPoints returned
    assert len(scoredAnomalies) == numRows
    assert all(isinstance(x, AnomalyPoint) for x in scoredAnomalies)

    # Expected number of points marked 'probationary'
    probationary = [x for x in scoredAnomalies if x.windowName == "probationary"]
    assert len(probationary) == o._getProbationaryLength(numRows)

    # Expected number of points marked 'in window'
    inWindow = [x for x in scoredAnomalies if x.windowName not in ("probationary", None)]
    assert len(inWindow) == expectedInWindowCount

    # Points in window have positive score; others have negative score
    for point in scoredAnomalies:
      if point.windowName not in ("probationary", None):
        assert point.sweepScore > 0
      else:
        assert point.sweepScore < 0

  def testPrepAnomalyListForScoring(self):
    fakeInput = [
      AnomalyPoint(0, 0.5, 0, 'probationary'),  # filter because 'probationary'
      AnomalyPoint(1, 0.5, 0, 'probationary'),  # filter because 'probationary'
      AnomalyPoint(2, 0.0, 0, None),
      AnomalyPoint(3, 0.1, 0, None),
      AnomalyPoint(4, 0.2, 0, 'windowA'),
      AnomalyPoint(5, 0.5, 0, 'windowB'),
      AnomalyPoint(6, 0.5, 0, None),
      AnomalyPoint(7, 0.0, 0, None),
    ]

    # Expected: sorted by anomaly score descending, with probationary rows filtered out.
    expectedList = [
      AnomalyPoint(5, 0.5, 0, 'windowB'),
      AnomalyPoint(6, 0.5, 0, None),
      AnomalyPoint(4, 0.2, 0, 'windowA'),
      AnomalyPoint(3, 0.1, 0, None),
      AnomalyPoint(2, 0.0, 0, None),
      AnomalyPoint(7, 0.0, 0, None),
    ]

    o = Sweeper()
    sortedList = prepAnomalyListForScoring(fakeInput)
    assert sortedList == expectedList

  def testPrepareScoreParts(self):
    fakeInput = [
      AnomalyPoint(0, 0.5, 0, 'probationary'),
      AnomalyPoint(1, 0.5, 0, 'probationary'),
      AnomalyPoint(2, 0.0, 0, None),
      AnomalyPoint(4, 0.2, 0, 'windowA'),
      AnomalyPoint(5, 0.2, 0, 'windowA'),
      AnomalyPoint(6, 0.5, 0, 'windowB'),
      AnomalyPoint(7, 0.5, 0, None),
    ]

    fakeFNWeight = 33.0
    o = Sweeper()
    o.fnWeight = fakeFNWeight

    # Expect one entry for all false positives and one entry per unique window name,
    # initialized to a starting score of `-self.fnWeight`
    expectedOutput = {
      "fp": 0,
      "windowA": -fakeFNWeight,
      "windowB": -fakeFNWeight
    }

    actualScoreParts = o._prepareScoreByThresholdParts(fakeInput)
    assert actualScoreParts == expectedOutput

  def testCalcScoreByThresholdReturnsExpectedScores(self):
    fnWeight = 5.0
    o = Sweeper()
    o.fnWeight = fnWeight

    fakeInput = [
      AnomalyPoint(0, 0.5, -1000, 'probationary'),  # Should never contribute to score (probationary)
      AnomalyPoint(1, 0.5, -1000, 'probationary'),  # Should never contribute to score (probationary)
      AnomalyPoint(2, 0.0, -3, None),  # Should never contribute to score (anomaly == 0.0)
      AnomalyPoint(4, 0.2, 20, 'windowA'),  # Should be used instead of next row when threshold <= 0.2
      AnomalyPoint(5, 0.3, 10, 'windowA'),  # Should be used for winowA _until_ threshold <= 0.2
      AnomalyPoint(6, 0.5, 5, 'windowB'),  # Only score for windowB, but won't be used until threshold <= 0.5
      AnomalyPoint(7, 0.5, -3, None),
    ]

    expectedScoresByThreshold = [
      ThresholdScore(1.1, -2 * fnWeight, 0, 2, 0, 3, 5),  # two windows, both false negatives at this threshold
      ThresholdScore(0.5, 5 - 3 - fnWeight, 1, 1, 1, 2, 5),  # Both 'anomalyScore == 0.5' score, windowA is still FN
      ThresholdScore(0.3, 5 - 3 + 10, 2, 1, 1, 1, 5),  # Both windows now have a TP
      ThresholdScore(0.2, 5 - 3 + 20, 3, 1, 1, 0, 5),  # windowA gets a new max value due to row 4 becoming active
      ThresholdScore(0.0, 5 - 3 + 20 - 3, 3, 0, 2, 0, 5),
    ]

    actual = o.calcScoreByThreshold(fakeInput)

    assert actual == expectedScoresByThreshold
