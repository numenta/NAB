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
import numpy

from scipy import stats

from nab.detectors.base import AnomalyDetector



class RelativeEntropyDetector(AnomalyDetector):

  """ This detector is an implementation of online anomaly detection using
  Relative Entropy statistic with multiple hypotheses as described in
  Figure 1 of Wang, Chengwei, et al. "Statistical Techniques for Online
  Anomaly Detection in Data Centers", Proceedings of the 8th ACM
  international conference on Autonomic computing. ACM, 2011.

  The algorithm is based on a hypothesis testing approach that compares
  observed data against multiple null hypotheses, representing frequencies of
  quantized data over a window. If the observed data is unseen and does not
  agree with any existing hypothesis, it is declared anomalous and a new
  hypothesis is created. Otherwise, it is declared non-anomalous, provided that
  the accepted hypothesis occurs frequently enough. Decision to accept/reject a
  null hypothesis is based on relative entropy compared against a threshold
  of acceptable false negative probability determined by the chi-squared
  distribution. Step-by-step details are given in code comments and parameters
  have been tuned for best performance of NAB.
  """

  def __init__(self, *args, **kwargs):
    """ Variable names are kept consistent with algorithm's pseudo code in
    the paper."""

    super(RelativeEntropyDetector, self).__init__(*args, **kwargs)

    # Timeseries of the metric on which anomaly needs to be detected
    self.util = []

    # Number of bins into which util is to be quantized
    self.N_bins = 5

    # Window size
    self.W = 52

    # Threshold against which the test statistic is compared. It is set to
    # the point in the chi-squared cdf with N-bins -1 degrees of freedom that
    #  corresponds to 0.99.
    self.T = stats.chi2.isf(0.01, self.N_bins - 1)

    # Threshold to determine if hypothesis has occured frequently enough
    self.c_th = 1

    # Tracks the current number of null hypothesis
    self.m = 0

    # Step size in time series quantization
    self.stepSize = (self.inputMax - self.inputMin) / self.N_bins

    # List of lists where P[i] indicates the empirical frequency of the ith
    # hypothesis.
    self.P = []

    # List where c[i] tracks the number of windows that agree with P[i]
    self.c = []


  def handleRecord(self, inputData):
    """ Returns a list of [anomalyScore] that takes a binary value of 0 or 1.
    The anomalyScore is determined based on the agreement of the observed data
    with existing hypotheses that occur frequently enough. Threshold to
    accept/reject a null hypothesis and declare an anomaly is determined by
    comparing the relative entropy of the observed data and all null
    hypothesis against the point on chi-squared distribution that
    corresponds to 0.99 (probability of incorrectly rejecting a
    null-hypothesis).
    """

    anomalyScore = 0.0
    self.util.append(inputData["value"])

    #  This check is for files where self.inputMin == self.input max i.e
    #  all data points are identical and stepSize is 0 e.g
    #  artificalNoAnomaly/art_flatline.csv file. Every point in such files
    #  is declared non-anomolous.
    if self.stepSize != 0.0:

      # All points in the first window are declared non-anomolous and
      # anomaly detection begins when length of data points seen is
      # greater than window length.
      if len(self.util) >= self.W:

        # Extracting current window
        util_current = self.util[-self.W:]

        # Quantize window data points into discretized bin values
        B_current = [math.ceil((c - self.inputMin) / self.stepSize) for c in
                     util_current]

        # Create a histogram of empirical frequencies for the current window
        # using B_current
        P_hat = numpy.histogram(B_current,
                                bins=self.N_bins,
                                range=(0,self.N_bins),
                                density=True)[0]

        # This is for the first null hypothesis
        if self.m == 0:
          self.P.append(P_hat)
          self.c.append(1)
          self.m = 1
        else:
          index = self.getAgreementHypothesis(P_hat)

          # Check if any null hypothesis is accepted or rejected
          if index != -1:

            # If hypothesis accepted, update counter for hypothesis that tracks
            # number of windows that have agreed to it so far.
            self.c[index] += 1

            # Check if hypothesis accepted occurs at least as frequently as
            # the given threshold. If not, classify data point as anomolous.
            if self.c[index] <= self.c_th:
              anomalyScore = 1.0
          else:

            # If all null hypothesis rejected, create new hypothesis based
            # on current window and update variables tracking hypothesis counts.
            anomalyScore = 1.0
            self.P.append(P_hat)
            self.c.append(1)
            self.m += 1

    return [anomalyScore]


  def getAgreementHypothesis(self,P_hat):
    """This function computes multinomial goodness-of-fit test. It calculates
    the relative entropy test statistic between P_hat and all `m` null
    hypothesis and compares it against the threshold `T` based on cdf of
    chi-squared distribution. The test relies on the observation that if the
    null hypothesis P is true, then as the number of samples grow the relative
    entropy converges to a chi-squared distribution1 with K-1 degrees of
    freedom.

    The function returns the index of hypothesis that agrees with minimum
    relative entropy. If all hypotheses disagree, the function returns -1.

    @param P_hat    (list)  Empirical frequencies of the current window.

    @return index   (int)   Index of the hypothesis with the minimum test
                            statistic.
    """

    index = -1
    minEntropy = float("inf")
    for i in xrange(self.m):
      entropy = 2 * self.W * stats.entropy(P_hat,self.P[i])
      if entropy < self.T and entropy < minEntropy:
        minEntropy = entropy
        index = i
    return index
