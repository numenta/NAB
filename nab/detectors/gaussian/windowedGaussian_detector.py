# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import math
import numpy

from nab.detectors.base import AnomalyDetector



def normalProbability(x, mean, std):
  """
  Given the normal distribution specified by the mean and standard deviation
  args, return the probability of getting samples > x. This is the
  Q-function: the tail probability of the normal distribution.
  """
  if x < mean:
    # Gaussian is symmetrical around mean, so flip to get the tail probability
    xp = 2*mean - x
    return normalProbability(xp, mean, std)

  # Calculate the Q function with the complementary error function, explained
  # here: http://www.gaussianwaves.com/2012/07/q-function-and-error-functions
  z = (x - mean) / std
  return 0.5 * math.erfc(z/math.sqrt(2))



class WindowedGaussianDetector(AnomalyDetector):
  """ A sliding window detector that computes anomaly score of a data point
  by computing its probability from the gaussian distribution over a window
  of previous data points. The windowSize is tuned to give best performance
  on NAB.
  """

  def __init__(self, *args, **kwargs):
    super(WindowedGaussianDetector, self).__init__(*args, **kwargs)

    self.windowSize = 6400
    self.windowData = []
    self.stepBuffer = []
    self.stepSize = 100
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
      anomalyScore = 1 - normalProbability(inputValue, self.mean, self.std)

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
    self.mean = numpy.mean(self.windowData)
    self.std = numpy.std(self.windowData)
    if self.std == 0.0:
      self.std = 0.000001
