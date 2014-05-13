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

import os
import pandas
import numpy

from optparse import OptionParser
from confusion_matrix import (WindowedConfusionMatrix,
                              pPrintMatrix)

try:
  from plotly import plotly
  from gef.utils.plotting import plotROC
except ImportError:
  plot = False

def genConfusionMatrix(results,
                       threshold = 0.99,
                       window = 30,
                       windowStepSize = 5,
                       costMatrix = None):
  '''
  Returns a confusion matrix object for the results of the
  given experiment and the ground truth labels.
  
    experiment      - an experiment info dict
    threshold       - float - cutoff to be applied to Likelihood scores
    window          - Use a WindowedConfusionMatrix and calculate stats over
                      this many minutes.
    windowStepSize  - The ratio of minutes to records
  '''
  
  labelName = 'label'
  columnNames = results.columns.tolist()
  if labelName not in columnNames:
    print columnNames
    raise Exception('No labels found. Expected a '
                    'column named "%s"' % labelName)
  
  # If likelihood is ABOVE threshold, label it an anomaly, otherwise not
  score = 'likelihood_score'
  predicted = results[score].apply(lambda x: 1 if x > threshold else 0)
  actual = results[labelName]

  if not windowStepSize:
    raise Exception("windowStepSize must be at least 1")
  
  cMatrix = WindowedConfusionMatrix(predicted,
                                    actual,
                                    window,
                                    windowStepSize,
                                    costMatrix)
  
  return cMatrix

def genCurveData(results,
                 minThresh = 0,
                 maxThresh = 1,
                 step = .01,
                 costMatrix = None):
  '''
  Returns a dict containing lists of data for plotting
  
    experiment - expInfo dict
    minThresh - Where to start our threshold search
    maxThresh - Where to stop the threshold search (inclusive)
    step - The increment size between each threshold test
  '''
  
  vals = {'tps': [],
           'tprs': [],
           'fprs': [],
           'ppvs': [],
           'thresholds': [],
           'costs': []}
  while minThresh <= maxThresh:
    cMatrix = genConfusionMatrix(results, minThresh, costMatrix = costMatrix)
    vals['tps'].append(cMatrix.tp)
    vals['tprs'].append(cMatrix.tpr)
    vals['fprs'].append(cMatrix.fpr)
    vals['ppvs'].append(cMatrix.ppv)
    vals['thresholds'].append(minThresh)
    vals['costs'].append(cMatrix.cost)
    minThresh += step
  
  return vals

def getCostMatrix():
  """
  Returns costs associated with each box in a confusion Matrix
  
  These matrix values have been picked to reflect realistic costs of reacting to
  each type of event for the streaming server monitoring data which comprise the
  NAB corpus.
  
  The cost matrix should be carefully considered for the given application
  and data to which it is applied.
  """
  
  costMatrix = {"tpCost": 0.0,
                "fpCost": 50.0,
                "fnCost": 100.0,
                "tnCost": 0.0}

  return costMatrix

def analyzeResults(options):
  """
  Generate ROC curve and find optimum point given cost matrix
  """
  with open(options.inputFile, 'r') as fh:
    results = pandas.read_csv(fh)
  
  costMatrix = getCostMatrix()
  vals = genCurveData(results,
                      options.min,
                      options.max,
                      options.step,
                      costMatrix)
  
  costs = vals['costs']
  print "The lowest expected cost with this ROC curve is: %s" % str(min(costs))
  costsArray = numpy.array(costs)
  minCostIndices = numpy.where(costsArray == costsArray.min())
  
  for minCostIndex in minCostIndices:
    ind = minCostIndex[0]
    print "A threshold that gives the minimum cost given the current cost matrix is: %s" % str(vals['thresholds'][ind])
  
  if options.plot:
    print "Generating ROC Curve Plot ..."
    # Get connection to plotly
    try:
      plotlyUser = os.environ['PLOTLY_USER_NAME']
      plotlyAPIKey = os.environ['PLOTLY_API_KEY']
    except KeyError:
      raise Exception("Plotly user name and api key were not found in "
            "your environment. Please add:\n"
            "export PLOTLY_USER_NAME={username}\n"
            "export PLOTLY_API_KEY={apikey}")
    
    py = plotly(username_or_email=plotlyUser,
                key=plotlyAPIKey,
                verbose = False)
    
    fileName = os.path.basename(options.inputFile)
    chartTitle = "ROC Curve: %s" % fileName
    plotROC(py, vals, chartTitle)


if __name__ == '__main__':
  # All the command line options
  parser = OptionParser(helpString)
  parser.add_option("--inputFile",
                    help="Path to data file. (default: %default)", 
                    dest="inputFile")
  parser.add_option("--outputFile",
                    help="Output file. Results will be written to this file."
                    " (default: %default)", 
                    dest="outputFile", default="analysis.csv")
  parser.add_option("--min", default=.998, type=float,
      help="Minimum value for classification threshold [default: %default]")
  parser.add_option("--max", default=.999, type=float,
      help="Maximum value for classification threshold [default: %default]")
  parser.add_option("--step", default=.0001, type=float,
      help="How much to increment the classification threshold for each point on the ROC curve. [default: %default]")
  parser.add_option("--plot", default=False, action="store_true",
                    help="Use the Plot.ly library to generate plots")

  options, args = parser.parse_args()
  
  # Main
  analyzeResults(options)
  
  

