# ----------------------------------------------------------------------
#  Copyright (C) 2013 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

import numpy
import math

class ConfusionMatrixBase(object):
  """
  Base class for the confusion matrices
  """
  
  def setPercentages(self):
    """
    Add in properties for percent representations of the confusion matrix
    """
    
    # Percent of total
    self.tpp = self.tp / self.count
    self.fpp = self.fp / self.count
    self.fnp = self.fn / self.count
    self.tnp = self.tn / self.count
  
  def setRates(self):
    """
    Add in properties for rates
    """

    # True Positive Rate / Sensitivity / Recall
    if self.tp or self.fn:
      self.tpr = self.tp / float(self.tp + self.fn)
    else:
      self.tpr = 0.0
    # False Positive Rate
    if self.fp or self.tn:      
      self.fpr = self.fp / float(self.fp + self.tn)
    else:
      self.fpr = 0.0
    # Positive Predictive Value / Precision
    # False Discovery Rate
    if self.tp or self.fp:
      self.ppv = self.tp / float(self.tp + self.fp)
      self.fdr = self.fp / float(self.tp + self.fp)
    else:
      self.ppv = self.fdr = 0.0
      
  def setCost(self, costMatrix, additionalCost = 0):
    """
    Determines and sets the total expected cost associated with a system
    represented by this confusion matrix.

    costMatrix - Cost values for each quadrent of the confusion matrix
    additionalCost - Any other calculated costs to add to the final total
    """
    
    self.cost = ((self.tp * costMatrix['tpCost']) +
                  (self.fp * costMatrix['fpCost']) +
                  (self.fn * costMatrix['fnCost']) +
                  (self.tn * costMatrix['tnCost']))

    self.cost += additionalCost

  def getTotal(self):
    """
    Total of counted records
    """
    
    return self.tp + self.fp + self.fn + self.tn + self.ignored


class WindowedConfusionMatrixV2(ConfusionMatrixBase):
  
  def __init__(self,
               predicted,
               actual,
               window,
               windowStepSize,
               costMatrix = None,
               verbosity = 0):
    """
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
    costMatrix      - A dict of costs for each quadrent of the confusion matrix
    verbosity       - How much output (if any) should be printed
    """
    self.tp = self.fp = self.fn = self.tn = self.ignored = 0.0
    
    # Default to even, zero-cost for each type of result
    if costMatrix == None:
      costMatrix = {"tpCost": 0.0,
                    "fpCost": 0.0,
                    "fnCost": 0.0,
                    "tnCost": 0.0}
      
    
    # Convert predicted and actual to numpy arrays if they are not
    predicted = numpy.array(predicted)
    actual = numpy.array(actual)
    
    # Label numbers and names
    aTypes = {1: 'handLabeledAnomaly'}
    ignoreTypes = {0.5: 'unclearRecord'}
    
    # How many records are in our window
    recordCount = window / windowStepSize
    
    # Per record late penalty is a fraction of a full false negative
    latePenalty = (.5 * costMatrix["fnCost"]) / recordCount

    # Go through all the results
    suppressDuration = recordCount
    self.count = len(actual)
    allowedWindow = 0
    suppresionWindow = 0
    latePenaltyTotal = 0
    for i, label in enumerate(actual):


      if allowedWindow and suppresionWindow:
        raise Exception("We should never be in both an allowed and supression "
                        "window at the same time.")

      # Are we waiting for the detector to catch an anomaly?
      if allowedWindow >= 1:
        if verbosity > 1: print i, "ALLOWED", predicted[i]
        # Did the detector catch the anomaly here?
        if predicted[i] == 1:
          if verbosity > 1: print "CAUGHT"
          self.tp += 1
          # Calculate the earned late penalty to this point
          latePenaltyTotal += (recordCount - allowedWindow) * latePenalty
          # Zero out the allowed window
          allowedWindow = 0
          # Start the suppression period
          suppresionWindow = suppressDuration
          suppresionPenaltyEarned = False
        # Detector didn't catch anomaly, continue countdown
        else:
          allowedWindow -= 1
          # If we've run out of window, the detector failed.
          if verbosity > 1: print allowedWindow
          if allowedWindow == 0:
            if verbosity > 1: print "FAILED"
            self.fn += 1
          else:
            self.tn += 1

        continue

      # Have we caught an anomaly and we want to avoid spam?
      elif suppresionWindow >= 1:
        if verbosity > 1: print i, "SUPRESS", predicted[i]
        # Have we already penalized the detector for spam?
        if suppresionPenaltyEarned:
          self.tn += 1
          suppresionWindow -= 1
        else:
          # Penalize the detector and set the penalty flag
          if predicted[i] == 1:
            if verbosity > 1: print "SPAM"
            self.fp += 1
            suppresionPenaltyEarned = True
          else:
            self.tn += 1

          # Count down our window
          suppresionWindow -= 1

        continue

      #######################################################################
      # Outside of allowed and suppression windows

      # Is this record the start of an anomaly? (ground truth)
      if verbosity > 1: print i, label, predicted[i]

      if label in aTypes.keys():

        # Is it caught immediately?
        if predicted[i] == 1:
          self.tp += 1
          # Start the suppression period
          suppresionWindow = suppressDuration
          suppresionPenaltyEarned = False
        # If not start the allowed window
        else:
          self.tn += 1
          allowedWindow = recordCount - 1

      # Is this an ambiguous record?
      elif label in ignoreTypes.keys():
        self.ignored += 1

      # This record is not an anomaly
      else:
        # If the detector thinks it is
        if predicted[i] == 1:
          if verbosity > 1: print "FALSE POSITIVE"
          self.fp += 1
        # If the detector got it correct
        else:
          self.tn += 1

      
    assert self.getTotal() == self.count

    self.setPercentages()
    self.setRates()
    self.setCost(costMatrix, math.floor(latePenaltyTotal))


class WindowedConfusionMatrix(ConfusionMatrixBase):
  
  def __init__(self,
               predicted,
               actual,
               window,
               windowStepSize,
               costMatrix = None):
    """
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
    costMatrix      - A dict of costs for each quadrent of the confusion matrix
    """
    self.tp = self.fp = self.fn = self.tn = self.ignored = 0.0
    
    # Default to even, zero-cost for each type of result
    if costMatrix == None:
      costMatrix = {"tpCost": 0.0,
                    "fpCost": 0.0,
                    "fnCost": 0.0,
                    "tnCost": 0.0}
      
    
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
    self.setCost(costMatrix)


 
def pPrintMatrix(matrix, title):
  """
  Prints a confusion matrix in a readable way
  
  matrix - A ConfusionMatrix object
  title - string - name to use for this matrix
  """
  
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