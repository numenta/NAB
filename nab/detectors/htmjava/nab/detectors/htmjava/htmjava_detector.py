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

import math
import simplejson as json
from subprocess import Popen, PIPE

from nupic.algorithms import anomaly_likelihood
from nupic.frameworks.opf.common_models.cluster_params import (
  getScalarMetricWithTimeOfDayAnomalyParams)

from nab.detectors.base import AnomalyDetector

# Fraction outside of the range of values seen so far that will be considered
# a spatial anomaly regardless of the anomaly likelihood calculation. This
# accounts for the human labelling bias for spatial values larger than what
# has been seen so far.
SPATIAL_TOLERANCE = 0.05


class HtmjavaDetector(AnomalyDetector):
  """
  Inspired by the 'NumentaDetector' replacing the 'OPF CLAModel' with a
  java subprocess running 'htm.java' model
  """
  def __init__(self, *args, **kwargs):

    super(HtmjavaDetector, self).__init__(*args, **kwargs)

    self.model = None
    self.sensorParams = None
    self.modelParams = None
    self.anomalyLikelihood = None
    # Keep track of value range for spatial anomaly detection
    self.minVal = None
    self.maxVal = None


  def getAdditionalHeaders(self):
    """Returns a list of strings."""
    return ["raw_score"]


  def handleRecord(self, inputData):
    """Returns a tuple (anomalyScore, rawScore).

    Internally to NuPIC "anomalyScore" corresponds to "likelihood_score"
    and "rawScore" corresponds to "anomaly_score". Sorry about that.
    """
    # Send input to HTM Java detector
    line = "{0},{1}\n".format(inputData['timestamp'], inputData['value'])
    self.model.stdin.writelines(line)

    # Get the value
    value = inputData["value"]

    # Retrieve the anomaly score
    result = self.model.stdout.readline()
    rawScore = float(result)

    # Update min/max values and check if there is a spatial anomaly
    spatialAnomaly = False
    if self.minVal != self.maxVal:
      tolerance = (self.maxVal - self.minVal) * SPATIAL_TOLERANCE
      maxExpected = self.maxVal + tolerance
      minExpected = self.minVal - tolerance
      if value > maxExpected or value < minExpected:
        spatialAnomaly = True
    if self.maxVal is None or value > self.maxVal:
      self.maxVal = value
    if self.minVal is None or value < self.minVal:
      self.minVal = value

    # Compute log(anomaly likelihood)
    anomalyScore = self.anomalyLikelihood.anomalyProbability(
      inputData["value"], rawScore, inputData["timestamp"])
    logScore = self.anomalyLikelihood.computeLogLikelihood(anomalyScore)
    if spatialAnomaly:
      logScore = 1.0

    return (logScore, rawScore)


  def initialize(self):
    # Get config params, setting the RDSE resolution
    rangePadding = abs(self.inputMax - self.inputMin) * 0.2
    self.modelParams = getScalarMetricWithTimeOfDayAnomalyParams(
      metricData=[0],
      minVal=self.inputMin-rangePadding,
      maxVal=self.inputMax+rangePadding,
      minResolution=0.001,
      tmImplementation="tm_cpp"
    )["modelConfig"]

    self._setupEncoderParams(
      self.modelParams["modelParams"]["sensorParams"]["encoders"])

    # Initialize the anomaly likelihood object
    numentaLearningPeriod = int(math.floor(self.probationaryPeriod / 2.0))
    self.anomalyLikelihood = anomaly_likelihood.AnomalyLikelihood(
      learningPeriod=numentaLearningPeriod,
      estimationSamples=self.probationaryPeriod-numentaLearningPeriod,
      reestimationPeriod=100
    )


  def _stopModel(self):
    """
    Stop HTM Java model process
    """
    if self.model:
      self.model.terminate()
      self.model = None


  def run(self):

    # Launch HTM Java detector per process passing OPF model parameters
    self.model = Popen(["java", "-jar",
                        "./nab/detectors/htmjava/build/libs/htm.java-nab.jar",
                        json.dumps(self.modelParams)],
                       stdin=PIPE, stdout=PIPE)

    response = super(HtmjavaDetector, self).run()

    # Terminate HTM Java
    self.model.stdin.writelines("\n")
    self._stopModel()
    return response


  def _setupEncoderParams(self, encoderParams):
    # The encoder must expect the NAB-specific datafile headers
    encoderParams["timestamp_dayOfWeek"] = encoderParams.pop("c0_dayOfWeek")
    encoderParams["timestamp_timeOfDay"] = encoderParams.pop("c0_timeOfDay")
    encoderParams["timestamp_timeOfDay"]["fieldname"] = "timestamp"
    encoderParams["timestamp_timeOfDay"]["name"] = "timestamp"
    encoderParams["timestamp_weekend"] = encoderParams.pop("c0_weekend")
    encoderParams["value"] = encoderParams.pop("c1")
    encoderParams["value"]["fieldname"] = "value"
    encoderParams["value"]["name"] = "value"

    self.sensorParams = encoderParams["value"]
