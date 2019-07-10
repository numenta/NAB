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

"""
This is implementation of the "naive forecast" is a baseline algorithm for time-series
forecasting. It repeats the last seen value. So `P(t+1) = P(t)`.
"""

from nab.detectors.base import AnomalyDetector

class NaiveDetector(AnomalyDetector):


  def initialize(self):
    super().initialize()
    self.predicted = 0.0 #previous value, last seen

  def handleRecord(self, inputData):
    """The anomaly score is simply the last seen value"""
    current = float(inputData["value"])
    inputData['predicted'] = self.predicted
    anomalyScore = 1 #FIXME how compute anomaly score from predicted, current?

    ret = [anomalyScore, self.predicted]
    self.predicted=current
    return (ret)

  def getAdditionalHeaders(self):
    return ['predicted']
