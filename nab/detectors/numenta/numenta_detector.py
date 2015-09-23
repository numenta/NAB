# ----------------------------------------------------------------------
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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
from nupic.frameworks.opf.modelfactory import ModelFactory

from nab.detectors.base import AnomalyDetector



class NumentaDetector(AnomalyDetector):

  def __init__(self, *args, **kwargs):

    super(NumentaDetector, self).__init__(*args, **kwargs)

    self.model = None
    self.sensorParams = None
    self.anomalyLikelihood = None


  def getAdditionalHeaders(self):
    """Returns a list of strings."""
    return ["raw_score"]


  def handleRecord(self, inputData):
    """Returns a tuple (anomalyScore, rawScore).

    Internally to NuPIC "anomalyScore" corresponds to "likelihood_score"
    and "rawScore" corresponds to "anomaly_score". Sorry about that.
    """
    # Send it to Numenta detector and get back the results
    result = self.model.run(inputData)

    # Retrieve the anomaly score and write it to a file
    rawScore = result.inferences["anomalyScore"]

    # Compute log(anomaly likelihood)
    anomalyScore = self.anomalyLikelihood.anomalyProbability(
      inputData["value"], rawScore, inputData["timestamp"])
    logScore = self.anomalyLikelihood.computeLogLikelihood(anomalyScore)

    return (logScore, rawScore)


  def initialize(self):
    calcRange = abs(self.inputMax - self.inputMin)
    calcPad = calcRange * .2

    self.inputMin = self.inputMin - calcPad
    self.inputMax = self.inputMax + calcPad
    # Load the model params JSON

    paramsPath = os.path.join(os.path.split(__file__)[0],
                "modelParams",
                "model_params.json")
    with open(paramsPath) as fp:
      modelParams = json.load(fp)

    self.sensorParams = modelParams["modelParams"]["sensorParams"]\
                                   ["encoders"]["value"]

    # RDSE - resolution calculation
    resolution = max(0.001,
                     (self.inputMax - self.inputMin) / \
                     self.sensorParams.pop("numBuckets")
                    )
    self.sensorParams["resolution"] = resolution

    self.model = ModelFactory.create(modelParams)

    self.model.enableInference({"predictedField": "value"})

    # Initialize the anomaly likelihood object
    numentaLearningPeriod = math.floor(self.probationaryPeriod / 2.0)
    self.anomalyLikelihood = anomaly_likelihood.AnomalyLikelihood(
      claLearningPeriod=numentaLearningPeriod,
      estimationSamples=self.probationaryPeriod-numentaLearningPeriod,
      reestimationPeriod=100
    )
