#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

helpString = """ This script takes a csv, a minimum threshold value, a maximum
threshold value, and a step value. It will generate an ROC curve given the csv
using each step between min and max. Finally it will find the point on that ROC
curve which minimizes the cost function defined below. """

from confusion_matrix import (WindowedConfusionMatrix,
                              pPrintMatrix)

def genConfusionMatrix(experiment,
                       threshold = 0.99,
                       window = 30,
                       windowStepSize = 5):
  '''
  Returns a confusion matrix object for the results of the
  given experiment and the ground truth labels.
  
    experiment      - an experiment info dict
    threshold       - float - cutoff to be applied to Likelihood scores
    window          - Use a WindowedConfusionMatrix and calculate stats over
                      this many minutes.
    windowStepSize  - The ratio of minutes to records
  '''
  
  results = getResultsFromExperiment(experiment)
  
  labelName = 'label'
  if labelName not in results.columns.tolist():
    raise Exception('No labels found in %s. Expected a '
                    'column named "%s"' % (resultsFile, labelName))
  
  # If likelihood is ABOVE threshold, label it an anomaly, otherwise not
  score = 'Likelihood Score'
  predicted = results[score].apply(lambda x: 1 if x > threshold else 0)
  actual = results[labelName]

  if not windowStepSize:
    raise Exception("windowStepSize must be at least 1")
  
  cMatrix = WindowedConfusionMatrix(predicted,
                                    actual,
                                    window,
                                    windowStepSize)
  
  return cMatrix

def genCurveData(experiment, minThresh = 0, maxThresh = 1, step = .01):
  '''
  Returns a dict containing lists of data for plotting
  
    experiment - expInfo dict
    minThresh - Where to start our threshold search
    maxThresh - Where to stop the threshold search
    step - The increment size between each threshold test
  '''
  
  vals = {'tps': [],
           'tprs': [],
           'fprs': [],
           'ppvs': [],
           'thresholds': []}
  while minThresh < maxThresh:
    cMatrix = genConfusionMatrix(experiment, minThresh)
    vals['tps'].append(cMatrix.tp)
    vals['tprs'].append(cMatrix.tpr)
    vals['fprs'].append(cMatrix.fpr)
    vals['ppvs'].append(cMatrix.ppv)
    vals['thresholds'].append(minThresh)
    minThresh += step
  
  return vals

def getResultsFromExperiment(experiment):
  '''
  Returns a Pandas DataFrame containing the results from the experiment
  '''
  # Get the results
  resultsFile = os.path.join(experiment['relativePath'],
                             experiment['resultsFilename'])
  with open(resultsFile, 'r') as fh:
    results = pandas.read_csv(fh)
  
  return results

def analyzeResults(options):
  """
  Generate ROC curve and find optimum point given cost matrix
  """
  pass


if __name__ == '__main__':
  # All the command line options
  parser = OptionParser(helpString)
  parser.add_option("--inputFile",
                    help="Path to data file. (default: %default)", 
                    dest="inputFile")
  parser.add_option("--outputFile",
                    help="Output file. Results will be written to this file."
                    " (default: %default)", 
                    dest="outputFile", default="results.csv")
  parser.add_option("--min", default=.9999, type=float,
      help="Minimum value for classification threshold [default: %default]")
  parser.add_option("--max", default=.999999, type=float,
      help="Maximum value for classification threshold [default: %default]")
  parser.add_option("--step", default=.000001, type=float,
      help="How much to increment the classification threshold for each point on the ROC curve. [default: %default]") 

  options, args = parser.parse_args()
  
  # Main
  analyzeResults(options)
  
  

