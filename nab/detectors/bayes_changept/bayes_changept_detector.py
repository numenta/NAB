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

import numpy
from scipy import stats

from nab.detectors.base import AnomalyDetector



class BayesChangePtDetector(AnomalyDetector):

  """ Implementation of the online Bayesian changepoint detection algorithm as
  described in Ryan P. Adams, David J.C. MacKay, "Bayesian Online Changepoint
  Detection", arXiv 0710.3742 (2007).

  The algorithm computes, for each record at step x in a data stream, the
  probability that the current record is part of a stream of length n for all
  n <= x. For a given record, if the maximimum of all the probabilities
  corresponds to a stream length of zero, the record represents a changepoint in
  the data stream. These probabilities are used to calculate anomaly scores for
  NAB results.

  The algorithm implemented here is a port from MATLAB code posted by R. Adams
  (http://hips.seas.harvard.edu/content/bayesian-online-changepoint-detection).
  It has been modified from the author's code to run online: rather than
  initializing a run-length matrix with the size of the dataset, we use an array
  that recursively overwrites old data (that is no longer needed by the
  algorithm). Calculating anomaly scores for this changepoint algorithm is not
  in the author's original code -- this is our own contribution.

  We started with the parameters specified in the publication above, as well as
  those found in the author's MATLAB implementation. Attempts at tuning these
  parameters showed insignificant change in the overall NAB score. The
  maxRunLength parameter (for this online implementation) was tuned to yield
  the best NAB score. We tried a variety of methods for calculating anomaly
  scores from run length probabilities, and implemented the best performing
  option -- discussed in the comments at the end of handleRecord().
  """

  def __init__(self, *args, **kwargs):

    super(BayesChangePtDetector, self).__init__(*args, **kwargs)

    # Setup the matrix that will hold our beliefs about the current
    # run lengths. We'll initialize it all to zero at first. For efficiency
    # we preallocate a data structure to hold only the info we need to detect
    # change points: columns for the current and next recordNumber, and a
    # sufficient number of rows (where each row represents probabilites of a
    # run of that length).
    self.maxRunLength = 500
    self.runLengthProbs = numpy.zeros((self.maxRunLength + 2, 2))
    # Record 0 is a boundary condition, where we know the run length is 0.
    self.runLengthProbs[0, 0] = 1.0

    # Init variables for state.
    self.recordNumber = 0
    self.previousMaxRun = 1

    # Define algorithm's helpers.
    self.observationLikelihoood = StudentTDistribution(alpha=0.1,
                                                       beta=0.001,
                                                       kappa=1.0,
                                                       mu=0.0)
    self.lambdaConst = 250
    self.hazardFunction = constantHazard


  def handleRecord(self, inputData):
    """ Returns a list [anomalyScore]. Algorithm details are in the comments."""
    # To accomodate this next record, shift the columns of the run length
    # probabilities matrix.
    if self.recordNumber > 0:
      self.runLengthProbs[:,0] = self.runLengthProbs[:,1]
      self.runLengthProbs[:,1] = 0

    # Evaluate the predictive distribution for the new datum under each of
    # the parameters. This is standard Bayesian inference.
    predProbs = self.observationLikelihoood.pdf(inputData["value"])

    # Evaluate the hazard function for this interval
    hazard = self.hazardFunction(self.recordNumber+1, self.lambdaConst)

    # We only care about the probabilites up to maxRunLength.
    runLengthIndex = min(self.recordNumber, self.maxRunLength)

    # Evaluate the growth probabilities -- shift the probabilities down and to
    # the right, scaled by the hazard function and the predictive probabilities.
    self.runLengthProbs[1:runLengthIndex+2, 1] = (
        self.runLengthProbs[:runLengthIndex+1, 0] *
        predProbs[:runLengthIndex+1] *
        (1-hazard)[:runLengthIndex+1]
    )

    # Evaluate the probability that there *was* a changepoint and we're
    # accumulating the probability mass back down at run length = 0.
    self.runLengthProbs[0, 1] = numpy.sum(
        self.runLengthProbs[:runLengthIndex+1, 0] *
        predProbs[:runLengthIndex+1] *
        hazard[:runLengthIndex+1]
    )

    # Renormalize the run length probabilities for improved numerical stability.
    self.runLengthProbs[:, 1] = (self.runLengthProbs[:, 1] /
                                 self.runLengthProbs[:, 1].sum())

    # Update the parameter sets for each possible run length.
    self.observationLikelihoood.updateTheta(inputData["value"])

    # Get the current run length with the highest probability.
    maxRecursiveRunLength = self.runLengthProbs[:, 1].argmax()

    # To calculate anomaly scores from run length probabilites we have several
    # options, implemented below:
    #   1. If the max probability for any run length is the run length of 0, we
    #   have a changepoint, thus anomaly score = 1.0.
    #   2. The anomaly score is the probability of run length 0.
    #   3. Compute a score by assuming a change in sequence from a previously
    #   long run is more anomalous than a change from a short run.
    # Option 3 results in the best anomaly detections (by far):
    if maxRecursiveRunLength < self.previousMaxRun:
      anomalyScore = 1 - (float(maxRecursiveRunLength) / self.previousMaxRun)
    else:
      anomalyScore = 0.0

    # Update state vars.
    self.recordNumber += 1
    self.previousMaxRun = maxRecursiveRunLength

    return [anomalyScore]



def constantHazard(arraySize, lambdaConst):
  """ The hazard function helps estimate the changepoint prior. Parameter
  lambdaConst is the timescale on the prior distribution of the changepoint.
  """
  return numpy.ones(arraySize) / float(lambdaConst)



class StudentTDistribution:

  def __init__(self, alpha, beta, kappa, mu):
    self.alpha0 = self.alpha = numpy.array([alpha])
    self.beta0 = self.beta = numpy.array([beta])
    self.kappa0 = self.kappa = numpy.array([kappa])
    self.mu0 = self.mu = numpy.array([mu])


  def pdf(self, data):
    """ Probability density function for the Student's T continuous random
    variable. More details here:
    http://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html
    """
    return stats.t.pdf(x=data,
                       df=2*self.alpha,
                       loc=self.mu,
                       scale=numpy.sqrt( (self.beta * (self.kappa+1)) /
                                         (self.alpha * self.kappa) )
                      )


  def updateTheta(self, data):
    """ Update parameters of the distribution."""
    muT0 = numpy.concatenate(
      (self.mu0, (self.kappa * self.mu + data) / (self.kappa + 1)))
    kappaT0 = numpy.concatenate((self.kappa0, self.kappa + 1.))
    alphaT0 = numpy.concatenate((self.alpha0, self.alpha + 0.5))
    betaT0 = numpy.concatenate((self.beta0, self.beta + (self.kappa * (data -
        self.mu)**2) / (2. * (self.kappa + 1.))))

    self.mu = muT0
    self.kappa = kappaT0
    self.alpha = alphaT0
    self.beta = betaT0
