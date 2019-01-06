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
import unittest

import pytest

from nab.sweep_optimizer import AnomalyPoint, Optimizer


class TestSweeper(object):
  def testOptimizerInit(self):
    o = Optimizer()
    assert o.probationPercent is not None

    o = Optimizer(probationPercent=0.30)
    assert o.probationPercent == 0.30

    o = Optimizer(costMatrix={"tpWeight": 0, "fpWeight": 1, "fnWeight": 2})
    assert o.tpWeight == 0
    assert o.fpWeight == 1
    assert o.fnWeight == 2

  @pytest.mark.parametrize("numRows,probationaryPercent,expectedLength", [
    (100, 0.0, 0),  # 0% probationary --> legnth 0
    (100, 1.0, 100),  # 100% --> length 100
    (100, 0.1, 10),
    (100, 0.15, 15),
    (5000, 0.1, 500),
    (6000, 0.1, 500),  # Cap at 5000 works as expected
  ])
  def testGetProbationaryLength(self, numRows, probationaryPercent, expectedLength):
    o = Optimizer(probationPercent=probationaryPercent)
    actualLength = o._getProbationaryLength(numRows)
    assert actualLength == expectedLength

  def testSetCostMatrix(self):
    o = Optimizer()
    assert o.tpWeight is None
    assert o.fpWeight is None
    assert o.fnWeight is None

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
    o = Optimizer(probationPercent=probationPercent, costMatrix=costMatrix)
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
        assert point.SweepScore > 0
      else:
        assert point.SweepScore < 0