
import math

from nab.detectors.base import AnomalyDetector
from CAD_OSE import CAD_OSE


class Cad_oseDetector(AnomalyDetector):
  """
  This detector uses Contextual Anomaly Detector - Open Source Edition
  https://github.com/smirmik/CAD
  """

  def handleRecord(self, inputData):

    anomalyScore = self.cad_ose.getAnomalyScore(inputData)
    return (anomalyScore,)

  def initialize(self):

    self.cad_ose = CAD_OSE   (  
        minValue = self.inputMin,
        maxValue = self.inputMax,
        restPeriod = self.probationaryPeriod / 5.0,
    )


