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
