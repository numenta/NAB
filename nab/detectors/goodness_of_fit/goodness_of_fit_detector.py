import numpy
from nab.detectors.base import AnomalyDetector

class GoodnessOfFitDetector(AnomalyDetector):
  def __init__(self, *args, **kwargs):
    super(GoodnessOfFitDetector, self).__init__(*args, **kwargs)

    self.W = 100
    self.W_index = 1
    self.N_bins = 100
    self.stepSize = (self.inputMax - self.inputMin)/self.numOfBins
    self.T = 0.95 #threshold for hypothesis testing
    self.util = [] # entire timeseries
    self.P = [] # matrix of all hypothesis
    self.c = [] # number of windows that agree with each of the hypothesis
    self.m = 0 #hypothesis count


  def handleRecord(self, inputData):
    anomalyScore = 0.0
    inputValue = inputData["value"]
    self.util.append(inputValue)
    if len(self.util) >= self.W:
      util_current = self.util[-self.W:]
      b_current = [(c - self.inputMin) / self.stepSize for c in util_current]
      print b_current



    return [anomalyScore]