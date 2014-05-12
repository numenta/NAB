# ----------------------------------------------------------------------
#  Copyright (C) 2013 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

import numpy

class ConfusionMatrixBase(object):
  '''
  Base class for the confusion matrices
  '''
  
  def setPercentages(self):
    '''
    Add in properties for percent representations of the confusion matrix
    '''
    
    # Percent of total
    self.tpp = self.tp / self.count
    self.fpp = self.fp / self.count
    self.fnp = self.fn / self.count
    self.tnp = self.tn / self.count
  
  def setRates(self):
    '''
    Add in properties for rates
    '''
    # Rates
    if self.tp or self.fn:
      self.tpr = self.tp / float(self.tp + self.fn)
    else:
      self.tpr = 0.0
    if self.fp or self.tn:      
      self.fpr = self.fp / float(self.fp + self.tn)
    else:
      self.fpr = 0.0
    if self.tp or self.fp:
      self.ppv = self.tp / float(self.tp + self.fp)
      self.fdr = self.fp / float(self.tp + self.fp)
    else:
      self.ppv = self.fdr = 0.0
      
  def setQualityScore(self,
                      tpWeight=100.0,
                      fpWeight=-50.0,
                      fnWeight=-10.0,
                      tnWeight=0.0):
    '''
    A heuristic to combine the confusion matrix into a single score.
    '''
    
    self.quality = ((self.tp * tpWeight) +
                    (self.fp * fpWeight) +
                    (self.fn * fnWeight) +
                    (self.tn * tnWeight))

  def getTotal(self):
    '''
    Total of counted records
    '''
    
    return self.tp + self.fp + self.fn + self.tn + self.ignored



class WindowedConfusionMatrix(ConfusionMatrixBase):
  
  def __init__(self, predicted, actual, window, windowStepSize):
    '''
     Generate the confusion matrix using the windowed method
    
     True Positives - An anomalous record followed in the next window minutes
                      by at least one above threshold likelihood score
                                           OR
                     Any likelihood score above threshold preceeded by an
                     an anomalous record within the last window minutes.
                     NOTE: We intentionally ignore this type of TP as we
                     don't want to optimize for it.
     False Negatives - Any anomalous record without an above threshold
                      likelihood score within the next window minutes
     False Positives - Any above threshold likelihood score preceeded by window
                       minutes without an anomalous record
     True Negatives - Any below threshold likelihood score preceeded by window
                      minutes without an anomalous record
                      
    predicted       - A list or numpy array
    actual          - A list or numpy array
    window          - Number of minutes we should calculate stats over
    windowStepSize  - Minutes per record
    '''
    self.tp = self.fp = self.fn = self.tn = self.ignored = 0.0
    
    # Convert predicted and actual to numpy arrays if they are not
    predicted = numpy.array(predicted)
    actual = numpy.array(actual)
    
    # Label numbers and names
    aTypes = {1: 'handLabeledAnomaly',
              2: 'injectedAnomaly'}
    ignoreTypes = {0.5: 'unclearRecord'}
    
    # How many records are in our window
    recordCount = window / windowStepSize
    
    # Go through all the results

    self.count = len(actual)
    for i, label in enumerate(actual):
      # This record is labeled as an anomaly
      # Look forward to see if it was caught
      if label in aTypes.keys():
        end = i + recordCount + 1
        if end > self.count:
          end = None
        # Are any results above threshold in the window?
        if any(predicted[i:end]):
          self.tp += 1
        else:
          self.fn += 1
      # Skip these records as they are ambiguous
      elif label in ignoreTypes.keys():
        self.ignored += 1
      # Look backward to see if there was an anomaly
      else:
        start = i - recordCount
        if start < 0:
          start = 0
        # Were any of the past window results anomalies?
        if any(actual[start:i] >= 1):
          # Ignore these cases as they are handled by forward looking logic
          # above
          self.ignored += 1
        else:
          # No anomaly in past window records, but above threshold
          if predicted[i]:
            self.fp += 1
          else:
            self.tn += 1
      
    assert self.getTotal() == self.count

    self.setPercentages()
    self.setRates()
    self.setQualityScore()


 
def pPrintMatrix(matrix, title):
  '''
  Prints a confusion matrix in a readable way
  
  matrix - A ConfusionMatrix object
  title - string - name to use for this matrix
  '''
  
  width = 50
  
  print '-' * width
  if title:
    print title
  print '\t\tP R E D I C T E D'
  print 'A\t\tNormal\t\tAnomaly'
  print 'C'
  print 'T  Normal\tTN:%.4f\tFP:%.4f' % (matrix.tn, matrix.fp)
  print 'U'
  print 'A  Anomaly\tFN:%.4f\tTP:%.4f'  % (matrix.fn, matrix.tp)
  print 'L'
  print '-' * width
  print '*' * width