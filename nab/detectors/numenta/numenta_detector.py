# ----------------------------------------------------------------------
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
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
    # print type(self.model)
    # print "inputData: %s" % str(inputData)
    # Send it to Numenta detector and get back the results
    result = self.model.run(inputData)

    # print "result: %s" % str(result)
    # Retrieve the anomaly score and write it to a file
    rawScore = result.inferences["anomalyScore"]

    # print "rawScore: %s" %(rawScore)
    # Compute the Anomaly Likelihood
    anomalyScore = self.anomalyLikelihood.likelihood(inputData["value"],
                                                     rawScore,
                                                     inputData["timestamp"])
    # print "anomalyScore: %s" % str(anomalyScore)

    return (anomalyScore, rawScore)


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

    # The anomaly likelihood object
    numentaLearningPeriod = math.floor(self.probationaryPeriod / 2.0)
    self.anomalyLikelihood = AnomalyLikelihood(self.probationaryPeriod,
                                               numentaLearningPeriod)

#############################################################################

class AnomalyLikelihood(object):
  """Helper class for running anomaly likelihood computation."""

  def __init__(self, probationaryPeriod = 600, numentaLearningPeriod = 300):
    """
    probationaryPeriod - no anomaly scores are reported for this many
    iterations.  This should be numentaLearningPeriod + some number of records
    for getting a decent likelihood estimation.

    numentaLearningPeriod - the number of iterations required for the Numenta
    detector to learn some of the patterns in the dataset.
    """
    self._iteration          = 0
    self._historicalScores   = []
    self._distribution       = None
    self._probationaryPeriod = probationaryPeriod
    self._numentaLearningPeriod  = numentaLearningPeriod


  def _computeLogLikelihood(self, likelihood):
    """
    Compute a log scale representation of the likelihood value. Since the
    likelihood computations return low probabilities that often go into 4 9"s or
    5 9"s, a log value is more useful for visualization, thresholding, etc.
    """
    # The log formula is:
    # Math.log(1.0000000001 - likelihood) / Math.log(1.0 - 0.9999999999);
    return math.log(1.0000000001 - likelihood) / -23.02585084720009


  def likelihood(self, value, anomalyScore, dttm):
    """
    Given the current metric value, plus the current anomaly score, output the
    anomalyLikelihood for this record.
    """
    dataPoint = (dttm, value, anomalyScore)
    # We ignore the first probationaryPeriod data points
    if len(self._historicalScores) < self._probationaryPeriod:
      likelihood = 0.5
    else:
      # On a rolling basis we re-estimate the distribution every 100 iterations
      if self._distribution is None or (self._iteration % 100 == 0):
        _, _, self._distribution = (
          anomaly_likelihood.estimateAnomalyLikelihoods(
            self._historicalScores,
            skipRecords = self._numentaLearningPeriod)
          )

      likelihoods, _, self._distribution = (
        anomaly_likelihood.updateAnomalyLikelihoods([dataPoint],
          self._distribution)
      )
      likelihood = 1.0 - likelihoods[0]

    # Before we exit update historical scores and iteration
    self._historicalScores.append(dataPoint)
    self._iteration += 1

    return likelihood