# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
This detector establishes a baseline score by recording a constant value for all
data points.
"""

from nab.detectors.base import AnomalyDetector



class NullDetector(AnomalyDetector):

  def handleRecord(self, inputData):
    """The anomaly score is simply a constant 0.5."""
    anomalyScore = 0.5
    return (anomalyScore, )
