# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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

"""TODO"""

import datetime
import unittest

from nab import scorer

COST_MATRIX = {
  "tpWeight": 1.1,
  "tnWeight": 1.0,
  "fpWeight": 0.11,
  "fnWeight": 1.2,
}



class ScorerTest(unittest.TestCase):


  @staticmethod
  def generateTimestamps(n):
    end = datetime.datetime(year=2016, month=7, day=5, hour=10)
    increment = datetime.timedelta(minutes=5)
    return [end - ((n-i) * increment) for i in xrange(n)]


  def testNull(self):
    timestamps = self.generateTimestamps(5)
    predictions = [0] * 5
    labels = [0] * 5
    windowLimits = []
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    self.assertAlmostEqual(0.0, score[1])


  def testFalsePositives(self):
    timestamps = self.generateTimestamps(5)
    predictions = [0, 1, 0, 1, 0]
    labels = [0] * 5
    windowLimits = []
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    self.assertAlmostEqual(-2.0 * COST_MATRIX["fpWeight"], score[1])


  def testFalseNegatives(self):
    timestamps = self.generateTimestamps(7)
    predictions = [0] * 7
    labels = [0, 1, 1, 0, 1, 1, 0]
    windowLimits = [(timestamps[1], timestamps[2]),
                    (timestamps[4], timestamps[5])]
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    self.assertAlmostEqual(-2.0 * COST_MATRIX["fnWeight"], score[1])


  def testFalsePositivesInProbationary(self):
    timestamps = self.generateTimestamps(5)
    predictions = [0, 1, 0, 1, 0]
    labels = [0] * 5
    windowLimits = []
    probationaryPeriod = 4
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    self.assertAlmostEqual(0.0, score[1])


  def testFalsePositivesBeforeAndAfterProbationary(self):
    timestamps = self.generateTimestamps(5)
    predictions = [0, 1, 0, 1, 0]
    labels = [0] * 5
    windowLimits = []
    probationaryPeriod = 3
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    self.assertAlmostEqual(-1.0 * COST_MATRIX["fpWeight"], score[1])


  def testTruePositives1(self):
    timestamps = self.generateTimestamps(7)
    predictions = [0, 0, 1, 0, 0, 0, 0]
    labels = [0, 1, 1, 0, 0, 0, 0]
    windowLimits = [(timestamps[1], timestamps[2])]
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    # These are calculated by multiplying the sigmoid of the relative
    # position in the window with the true positive weight. The sigmoid
    # values are hard coded here but were calculated by running
    # nab.scorer.scaledSigmoid. The divisor is scaledSigmoid(-1.0).
    firstWindowScore = (0.8482836399575131 * COST_MATRIX["tpWeight"] /
                        0.9866142981514305)
    self.assertAlmostEqual(firstWindowScore, score[1])


  def testTruePositives1WithFN(self):
    timestamps = self.generateTimestamps(7)
    predictions = [0, 0, 1, 0, 0, 0, 0]
    labels = [0, 1, 1, 0, 1, 1, 0]
    windowLimits = [(timestamps[1], timestamps[2]),
                    (timestamps[4], timestamps[5])]
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    # These are calculated by multiplying the sigmoid of the relative
    # position in the window with the true positive weight. The sigmoid
    # values are hard coded here but were calculated by running
    # nab.scorer.scaledSigmoid. The divisor is scaledSigmoid(-1.0).
    firstWindowScore = (0.8482836399575131 * COST_MATRIX["tpWeight"] /
                        0.9866142981514305)
    secondWindowScore = -1.0 * COST_MATRIX["fnWeight"]
    self.assertAlmostEqual(firstWindowScore + secondWindowScore, score[1])


  def testTruePositives2(self):
    timestamps = self.generateTimestamps(7)
    predictions = [0, 0, 0, 0, 1, 0, 0]
    labels = [0, 0, 0, 0, 1, 1, 0]
    windowLimits = [(timestamps[4], timestamps[5])]
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    # These are calculated by multiplying the sigmoid of the relative
    # position in the window with the true positive weight. The sigmoid
    # values are hard coded here but were calculated by running
    # nab.scorer.scaledSigmoid. The divisor is scaledSigmoid(-1.0).
    secondWindowScore = (0.9866142981514305 * COST_MATRIX["tpWeight"] /
                         0.9866142981514305)
    self.assertAlmostEqual(secondWindowScore, score[1])


  def testTruePositives3(self):
    timestamps = self.generateTimestamps(7)
    predictions = [0, 0, 0, 0, 1, 1, 0]
    labels = [0, 0, 0, 0, 1, 1, 0]
    windowLimits = [(timestamps[4], timestamps[5])]
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    # These are calculated by multiplying the sigmoid of the relative
    # position in the window with the true positive weight. The sigmoid
    # values are hard coded here but were calculated by running
    # nab.scorer.scaledSigmoid. The divisor is scaledSigmoid(-1.0).
    secondWindowScore = (0.9866142981514305 * COST_MATRIX["tpWeight"] /
                         0.9866142981514305)
    self.assertAlmostEqual(secondWindowScore, score[1])


  def testTruePositivesMultiple(self):
    timestamps = self.generateTimestamps(7)
    predictions = [0, 0, 1, 0, 1, 0, 0]
    labels = [0, 1, 1, 0, 1, 1, 0]
    windowLimits = [(timestamps[1], timestamps[2]),
                    (timestamps[4], timestamps[5])]
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    # These are calculated by multiplying the sigmoid of the relative
    # position in the window with the true positive weight. The sigmoid
    # values are hard coded here but were calculated by running
    # nab.scorer.scaledSigmoid. The divisor is scaledSigmoid(-1.0).
    firstWindowScore = (0.8482836399575131 * COST_MATRIX["tpWeight"] /
                        0.9866142981514305)
    secondWindowScore = (0.9866142981514305 * COST_MATRIX["tpWeight"] /
                         0.9866142981514305)
    self.assertAlmostEqual(firstWindowScore + secondWindowScore, score[1])


  def testFalsePositiveAfterWindow1(self):
    timestamps = self.generateTimestamps(5)
    predictions = [0, 0, 0, 0, 1]
    labels = [0, 1, 1, 0, 0]
    windowLimits = [(timestamps[1], timestamps[2])]
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    firstWindowScore = -1.0 * COST_MATRIX["fnWeight"]
    # These are calculated by multiplying the sigmoid of the relative
    # position in the window with the true positive weight. The sigmoid
    # values are hard coded here but were calculated by running
    # nab.scorer.scaledSigmoid.
    fpScore = -0.9999092042625951 * COST_MATRIX["fpWeight"]
    self.assertAlmostEqual(firstWindowScore + fpScore, score[1])


  def testFalsePositiveAfterWindow2(self):
    timestamps = self.generateTimestamps(5)
    predictions = [0, 0, 0, 1, 0]
    labels = [0, 1, 1, 0, 0]
    windowLimits = [(timestamps[1], timestamps[2])]
    probationaryPeriod = 0
    score = scorer.Scorer(timestamps, predictions, labels, windowLimits,
                          COST_MATRIX, probationaryPeriod).getScore()
    firstWindowScore = -1.0 * COST_MATRIX["fnWeight"]
    # These are calculated by multiplying the sigmoid of the relative
    # position in the window with the true positive weight. The sigmoid
    # values are hard coded here but were calculated by running
    # nab.scorer.scaledSigmoid.
    fpScore = -0.9866142981514303 * COST_MATRIX["fpWeight"]
    self.assertAlmostEqual(firstWindowScore + fpScore, score[1])



if __name__ == "__main__":
  unittest.main()
