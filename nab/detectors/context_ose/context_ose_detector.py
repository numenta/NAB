# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from nab.detectors.base import AnomalyDetector
from nab.detectors.context_ose.cad_ose import ContextualAnomalyDetectorOSE

class ContextOSEDetector(AnomalyDetector):
  
  """
  This detector uses Contextual Anomaly Detector - Open Source Edition
  2016, Mikhail Smirnov   smirmik@gmail.com
  https://github.com/smirmik/CAD
  """

  def __init__(self, *args, **kwargs):

    super(ContextOSEDetector, self).__init__(*args, **kwargs)

    self.cadose = None

  def handleRecord(self, inputData):

    anomalyScore = self.cadose.getAnomalyScore(inputData)
    return (anomalyScore,)

  def initialize(self):

    self.cadose = ContextualAnomalyDetectorOSE (
      minValue = self.inputMin,
      maxValue = self.inputMax,
      restPeriod = self.probationaryPeriod / 5.0,
    )
