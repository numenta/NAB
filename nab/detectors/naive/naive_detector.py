# ----------------------------------------------------------------------
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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

import math #exp

from nab.detectors.base import AnomalyDetector

EPSILON = 0.00000001

class NaiveDetector(AnomalyDetector):
  """
  This is implementation of the "naive forecast", aka "random walk forecasting",
  which is a baseline algorithm for time-series forecasting. 
  It predicts the last seen value. So `Prediction(t+1) = Input(t)`.
  
  Hyperparameter to optimize is @param coef in `initialize`.
  """


  def initialize(self, coef=10.0):
    """
    @param `coef` for the activation function that scales anomaly score to [0, 1.0]
           The function is: `anomalyScore = 1-exp(-coef*x)`, where 
           `x=abs(current - predicted)/predicted`. 
    """
    super().initialize()
    self.predicted = 0.0 #previous value, last seen
    self.coef = coef


  def handleRecord(self, inputData):
    """The predicted value is simply the last seen value,
       Anomaly score is computed as a function of current,predicted.

       See @ref `initialize` param `coef`.
    """
    current = float(inputData["value"])
    inputData['predicted'] = self.predicted
    try:
      anomalyScore = self.anomalyFn_(current, self.predicted)
    except: 
      #on any math error (overflow,...), we mark this as anomaly. tough love
      anomalyScore = 1.0

    ret = [anomalyScore, self.predicted]
    self.predicted=current
    return (ret)


  def getAdditionalHeaders(self):
    return ['predicted']


  def anomalyFn_(self, current, predicted):
    """
    compute anomaly score from 2 scalars
    """
    if predicted == 0.0:
      predicted = EPSILON #avoid division by zero

    # the computation
    x = abs(current - predicted)/predicted
    score = 1-math.exp(-self.coef * x)

    # bound to anomaly range (should not happen, but some are over)
    if(score > 1):
        score = 1.0
    elif(score < 0):
        score = 0.0

    print(score)
    assert(score >= 0 and score <= 1)
    return score

