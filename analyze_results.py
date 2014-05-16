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
import sys
import csv

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
                       costMatrix = None,
                       verbosity = 0):
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

  if verbosity > 0:
    pPrintMatrix(cMatrix, threshold)
  
  return cMatrix

def genCurveData(results,
                 minThresh = 0,
                 maxThresh = 1,
                 step = .1,
                 costMatrix = None,
                 verbosity = 0):
  '''
  Returns a dict containing lists of data for plotting
  
  experiment - expInfo dict
  minThresh - Where to start our threshold search
  maxThresh - Where to stop the threshold search (inclusive)
  step - The increment size between each threshold test
  '''
  
  vals = {'tprs': [],
           'fprs': [],
           'thresholds': [],
           'costs': []}

  incrementCount = 1.0
  while minThresh < maxThresh and incrementCount < 60:
    cMatrix = genConfusionMatrix(results,
                                 minThresh, 
                                 costMatrix = costMatrix,
                                 verbosity = verbosity)
    vals['tprs'].append(cMatrix.tpr)
    vals['fprs'].append(cMatrix.fpr)
    vals['thresholds'].append(minThresh)
    vals['costs'].append(cMatrix.cost)
    minThresh += step
    # Decrease step as we approach 1
    if incrementCount % 9 == 0:
      step /= 10.0
    incrementCount += 1.0
  
  return vals

def getCostMatrix():
  """
  Returns costs associated with each box in a confusion Matrix
  
  These values have been picked to reflect realistic costs of reacting to
  each type of event for the server monitoring data which comprise the
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

  # Ensure at least one file and all files are csv
  if not options.resultsFile and options.resultsDir is None:
    print("Requires at least one argument of csv files to use.")
    sys.exit(1)
  elif options.resultsFile:
    if (options.resultsFile.split('.') < 2 or 
      options.resultsFile.split('.')[-1] != 'csv'):
      print("File is not a csv.")
      sys.exit(1)
    else:
      csvFiles = [options.resultsFile]
  elif options.resultsDir:
    # Search directory for csv files
    items = os.listdir(options.resultsDir)
    csvFiles = [os.path.join(options.resultsDir, item) for
                item in items if item[-4:] == '.csv']

  # Accumulate results
  header = None
  resultsSummary = []

  # Loop over all specified results files
  for resultsFile in csvFiles:

    with open(resultsFile, 'r') as fh:
      results = pandas.read_csv(fh)
    
    costMatrix = getCostMatrix()
    vals = genCurveData(results,
                        options.min,
                        options.max,
                        options.step,
                        costMatrix, 
                        options.verbosity)

    # First time through write out the headers
    if not header:
      header = ['Name']
      thresholds = vals['thresholds']
      header.extend(thresholds)
      resultsSummary.append(header)

    # Add a row for each file processed
    resultRow = [resultsFile]
    resultRow.extend(vals['costs'])
    resultsSummary.append(resultRow)
    
    costs = vals['costs']
    costsArray = numpy.array(costs)
    minCostIndices = numpy.where(costsArray == costsArray.min())
    
    for minCostIndex in minCostIndices:
      ind = minCostIndex[0]
    
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
      
      fileName = os.path.basename(resultsFile)
      chartTitle = "ROC Curve: %s" % fileName
      plotROC(py, vals, chartTitle)

  # Sum all values
  resultsSummaryArray = numpy.array(resultsSummary)
  # Skip first row and column
  summaryView = resultsSummaryArray[1:,1:].astype('float')
  totalsArray = numpy.sum(summaryView, axis=0)
  totalsList = totalsArray.tolist()
  print "Minimum cost:",
  lowestCost = totalsArray.min()
  print lowestCost
  minSummaryCostIndices = numpy.where(totalsArray == lowestCost)[0].tolist()
  print "Best thresholds:"
  for ind in minSummaryCostIndices:
    print "\t" + str(thresholds[ind])

  # Write out all our results
  with open(options.outputFile, 'w') as outFile:

    writer = csv.writer(outFile)
    writer.writerows(resultsSummary)
    totalsRow = ['Totals']
    totalsRow.extend(totalsList)
    writer.writerow(totalsRow)

if __name__ == '__main__':
  # All the command line options
  parser = OptionParser(helpString)
  parser.add_option("-f", "--resultsFile",
                    help="Path to a single results file to analyze.")
  parser.add_option("-d", "--resultsDir",
                    help="Path to results files. (default: %default)")
  parser.add_option("-o", "--outputFile",
                    help="Output file. Results will be written to this file."
                    " (default: %default)", 
                    default="resultsSummary.csv")
  parser.add_option("--min", default=0.0, type=float,
      help="Minimum value for classification threshold [default: %default]")
  parser.add_option("--max", default=1, type=float,
      help="Maximum value for classification threshold [default: %default]")
  parser.add_option("--step", default=.1, type=float,
      help="How much to increment the classification threshold for each point on the ROC curve. [default: %default]")
  parser.add_option("--plot", default=False, action="store_true",
                    help="Use the Plot.ly library to generate plots")
  parser.add_option("--verbosity", default=0, help="Increase the amount and "
                    "detail of output by setting this greater than 0.")

  options, args = parser.parse_args()
  
  # Main
  analyzeResults(options)