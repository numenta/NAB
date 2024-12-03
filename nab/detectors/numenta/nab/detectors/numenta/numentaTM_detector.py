# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import os
import math
import simplejson as json

from nupic.algorithms import anomaly_likelihood
from nupic.frameworks.opf.common_models.cluster_params import (
  getScalarMetricWithTimeOfDayAnomalyParams)
try:
  from nupic.frameworks.opf.model_factory import ModelFactory
except:
  # Try importing it the old way (version < 0.7.0.dev0)
  from nupic.frameworks.opf.modelfactory import ModelFactory

from nab.detectors.numenta.numenta_detector import NumentaDetector



class NumentaTMDetector(NumentaDetector):
  """
  This detector uses the implementation of temporal memory in
  https://github.com/numenta/nupic.core/blob/master/src/nupic/algorithms/TemporalMemory.hpp.
  It differs from its parent detector in temporal memory and its parameters.
  """

  def __init__(self, *args, **kwargs):

    super(NumentaTMDetector, self).__init__(*args, **kwargs)


  def initialize(self):
    # Get config params, setting the RDSE resolution
    rangePadding = abs(self.inputMax - self.inputMin) * 0.2

    modelParams = getScalarMetricWithTimeOfDayAnomalyParams(
      metricData=[0],
      minVal=self.inputMin-rangePadding,
      maxVal=self.inputMax+rangePadding,
      minResolution=0.001,
      tmImplementation="tm_cpp"
    )["modelConfig"]

    self._setupEncoderParams(
      modelParams["modelParams"]["sensorParams"]["encoders"])

    self.model = ModelFactory.create(modelParams)

    self.model.enableInference({"predictedField": "value"})

    # Initialize the anomaly likelihood object
    numentaLearningPeriod = int(math.floor(self.probationaryPeriod / 2.0))
    self.anomalyLikelihood = anomaly_likelihood.AnomalyLikelihood(
      learningPeriod=numentaLearningPeriod,
      estimationSamples=self.probationaryPeriod-numentaLearningPeriod,
      reestimationPeriod=100
    )
