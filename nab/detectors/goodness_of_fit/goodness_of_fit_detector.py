import numpy
import math
from scipy import stats

from nab.detectors.base import AnomalyDetector

class GoodnessOfFitDetector(AnomalyDetector):

  """ This detector is an implementation of ...
      Tried to use the same variable names as the paper
  """

  def __init__(self, *args, **kwargs):
    super(GoodnessOfFitDetector, self).__init__(*args, **kwargs)

    self.W = 52
    self.N_bins = 5.0
    self.c_th = 1
    self.stepSize = (self.inputMax - self.inputMin)/self.N_bins
    self.T = stats.chi2.isf(0.01, self.N_bins - 1)  #set to that point in the
    #  chi-squared cdf with bins - 1 degrees of freedom that
    # corresponds to 0.95 or 0.99. isf is inverse survival function which is
    # 1 - cdf.
    self.util = [] # entire timeseries
    self.P = [] # matrix of hypothesis. each row is a hypothesis
    self.c = [] # agreement counter for each of the hypothesis
    self.m = 0 #total hypothesis count


  def handleRecord(self, inputData):
    """ Returns a list [anomalyScore] calculated using a kernel based
      similarity method described in the comments below"""

    anomalyScore = 0.0 # first window non anomolous
    inputValue = inputData["value"]
    self.util.append(inputValue)
    if self.stepSize != 0.0: # i.e min != max
      if len(self.util) >= self.W:
        util_current = self.util[-self.W:]
        B_current = [math.ceil((c - self.inputMin) / self.stepSize) for c in
                     util_current]

        P_hat = numpy.histogram(B_current,
                                bins=self.N_bins,
                                range=(0,self.N_bins),
                                density=True)[0]

        if self.m == 0:
          # for first hypothesis
          self.P.append(P_hat)
          self.c.append(1)
          self.m = 1
        else:
          index = self.getAgreementHypothesis(P_hat)
          if index != -1:
            # Hypothesis agrees to an existing one
            self.c[index] += 1
            if self.c[index] <= self.c_th:
              anomalyScore = 1.0
          else:
            # no existing hypothesis with agreement found, add new one
            anomalyScore = 1.0
            self.P.append(P_hat)
            self.c.append(1)
            self.m += 1

    return [anomalyScore]

  def getAgreementHypothesis(self,P_hat):
    """
    TO DO HERE
    @param p_current:
    @return: index for the minimum hypothesis
    """
    index = -1
    minEntropy = float("inf")
    for i in range(0,self.m):
      entropy = 2 * self.W * stats.entropy(P_hat,self.P[i])
      if entropy < self.T and entropy < minEntropy:
        minEntropy = entropy
        index = i
    return index
