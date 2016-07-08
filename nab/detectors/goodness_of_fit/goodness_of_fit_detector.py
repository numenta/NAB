import numpy
import math
from nab.detectors.base import AnomalyDetector

class GoodnessOfFitDetector(AnomalyDetector):
  def __init__(self, *args, **kwargs):
    super(GoodnessOfFitDetector, self).__init__(*args, **kwargs)

    self.W = 100
    self.W_index = 1
    self.N_bins = 100.0
    self.stepSize = (self.inputMax - self.inputMin)/self.N_bins
    self.T = 0.95 #threshold for hypothesis testing
    self.c_threshold = 2
    self.util = [] # entire timeseries
    self.P = [] # matrix of all hypothesis
    self.c = [] # number of windows that agree with each of the hypothesis
    self.m = 0 #hypothesis count
    self.count = 1 #data point count


  def handleRecord(self, inputData):
    anomalyScore = 0.0 # for now, first window all data points labeled as
    # unanomolous
    inputValue = inputData["value"]
    self.util.append(inputValue)
    if len(self.util) >= self.W:
      util_current = self.util[-self.W:]
      b_current = [math.ceil((c - self.inputMin) / self.stepSize) for c in
                   util_current]
      # print "Counter : ", self.count
      # print "B_current : ", b_current
      (p_current_hist,p_current_edges) = numpy.histogram(b_current, bins =
      self.N_bins,range = (0.0, self.N_bins))
      # print "P_current : ", p_current_hist
      # print "non-zero index", numpy.nonzero(p_current_hist)

      if self.m == 0:
        self.P[0] = p_current_hist
        self.c[0] = 1
        self.m = 1
      elif self.getAgreementHypothesis(p_current_hist) != -1:
        # if an existing hypothesis agree, no new hypothesis added,
        #write function and update else ifs and rename varaibles
        self.c[idx] += 1
        if self.c[idx] <= self.c_threshold:
          anomalyScore = 1.0
      else:
        anomalyScore = 1.0
        self.P[self.m] = p_current_hist
        self.c[self.m] = 1
        self.m += 1

    self.count +=1
    return [anomalyScore]

  def getAgreementHypothesis(self,p_current):
    for hypothesis in self.P:


    return True