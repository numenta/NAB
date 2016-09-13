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
