# ----------------------------------------------------------------------
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

import numpy as np
from nab.detectors.base import AnomalyDetector
from nupic.algorithms import anomaly_likelihood



class WindowedGaussianDetector(AnomalyDetector):
  """ A sliding window detector that computes anomaly score of a data point
  by computing its probability from the gaussian distribution over a window
  of previous data points. The windowSize is tuned to give best performance
  on NAB.
  """

  def __init__(self, *args, **kwargs):
    # Initialize the parent
    super(WindowedGaussianDetector, self).__init__(*args, **kwargs)

    self.windowSize = 20
    self.windowData = []
    self.stepBuffer = []
    self.stepSize = 1
    self.mean = 0
    self.std = 1


  def handleRecord(self, inputData):
    """Returns a tuple (anomalyScore).
    The anomalyScore is the tail probability of the gaussian (normal) distribution
    over a sliding window of inputData values. The tail probability is based on the
    Q-function. The windowSize has been tuned to give best performance on NAB.
    """

    anomalyScore = 0.0
    inputValue = inputData["value"]
    if len(self.windowData) > 0:
      anomalyScore = 1 - anomaly_likelihood.normalProbability(inputValue,
                                                          {"mean": self.mean, "stdev": self.std})

    if len(self.windowData) < self.windowSize:
      self.windowData.append(inputValue)
      self._updateWindow()
    else:
      self.stepBuffer.append(inputValue)
      if len(self.stepBuffer) == self.stepSize:
        # slide window forward by stepSize
        self.windowData = self.windowData[self.stepSize:]
        self.windowData.extend(self.stepBuffer)
        # reset stepBuffer
        self.stepBuffer = []
        self._updateWindow()

    return (anomalyScore, )


  def _updateWindow(self):
    self.mean = np.mean(self.windowData)
    self.std = np.std(self.windowData)
    if self.std == 0.0:
      self.std = 0.000001





