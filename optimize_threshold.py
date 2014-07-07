#!/usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

helpString = """ This script takes a batch of csvs and generates an ROC curve
given the csvs using steps between thresholds of 0.0 and 1.0. Finally it will
find the point on that ROC curve which minimizes the cost function defined
below. """

import os
import pandas
import numpy
import sys
import csv
import yaml

from optparse import OptionParser
from pprint import pprint
from confusion_matrix import (WindowedConfusionMatrix,
                              pPrintMatrix)
from helpers import (getDataGroupDirs,
                     inferDetector)

gPlotsAvailable = False
try:
  from plotly import plotly as py
  from plotly.graph_objs import (Data,
                                 Layout,
                                 Figure,
                                 Trace,
                                 XAxis,
                                 YAxis)
  gPlotsAvailable = True
except ImportError:
  print "Plotly not installed. Plots will not be available."


def optimizeThreshold(options):
  """
  Generate ROC curve and find optimum point given cost matrix. Results of
  this analysis will be put into a best and a summary results file.
  """

  # Load the config file
  with open(options.config) as configHandle:
    config = yaml.load(configHandle)

  # Update any missing config values from global config file
  if not options.resultsDir:
    options.resultsDir = config["ResultsDirectory"]

  options.detectors = config["AnomalyDetectors"]

  # Thresholds
  threshMin = 0.0
  threshMax = 1.0
  initialThreshStep = .1

  dataGroupDirs = getDataGroupDirs(options.resultsDir, options.detectors)

  print dataGroupDirs

  # Infer which detector generated these results from the path
  detector = inferDetector(options.resultsDir, options.detectors)

  csvFiles = []
  for dataGroupDir in dataGroupDirs:
    rawDir = os.path.join(dataGroupDir, 'raw')
    items = os.listdir(rawDir)
    files = [os.path.join(rawDir, item) for
                item in items if item[-4:] == '.csv']
    csvFiles.extend(files)

  if not csvFiles:
    print("No files to analyze.")
    sys.exit(0)

  # Accumulate results
  header = None
  resultsSummary = []

  # Loop over all specified results files
  for resultsFile in csvFiles:

    print "Analyzing results file %s ..." % resultsFile
    with open(resultsFile, 'r') as fh:
      results = pandas.read_csv(fh)
    
    costMatrix = getCostMatrix(config)
    vals = genCurveData(results,
                        threshMin,
                        threshMax,
                        initialThreshStep,
                        config['ScoringWindow'],
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
      
      py.sign_in(plotlyUser, plotlyAPIKey)
      
      fileName = os.path.basename(resultsFile)
      chartTitle = "ROC Curve: %s" % fileName
      plotROC(py, vals, chartTitle)

  # Sum all values
  resultsSummaryArray = numpy.array(resultsSummary)

  # Skip first row and column
  summaryView = resultsSummaryArray[1:,1:].astype('float')
  
  # Summarize data for file writing
  totalsArray = numpy.sum(summaryView, axis=0)
  totalsList = totalsArray.tolist()
  lowestCost = totalsArray.min()
  minSummaryCostIndices = numpy.where(totalsArray == lowestCost)[0].tolist()
  bestThresholds = [thresholds[ind] for ind in minSummaryCostIndices]

  # Re-run all files with lowest "best" threshold
  minThresh = bestThresholds[0]
  detailedResults = []
  headers = ["Results File",
             "True Positives",
             "False Positives",
             "False Negatives",
             "True Negatives",
             "Cost",
             "Total Normal",
             "Total Anomalous"]
  detailedResults.append(headers)
  for resultsFile in csvFiles:

    with open(resultsFile, 'r') as fh:
      results = pandas.read_csv(fh)
    
    costMatrix = getCostMatrix(config)
    cMatrix = genConfusionMatrix(results,
                                 minThresh,
                                 window = config['ScoringWindow'],
                                 costMatrix = costMatrix)

    # TODO - Calculate the total norm vs anomalous directly from labels
    detailedResults.append([resultsFile,
                            cMatrix.tp, 
                            cMatrix.fp,
                            cMatrix.fn,
                            cMatrix.tn,
                            cMatrix.cost,
                            cMatrix.tn + cMatrix.fp,
                            cMatrix.tp + cMatrix.fn])

  # Write out detailed results
  detailedResultsArray = numpy.array(detailedResults)

  # Skip first row and column
  detailedView = detailedResultsArray[1:,1:].astype('float')
  
  # Summarize data for file writing
  detailedTotalsArray = numpy.sum(detailedView, axis=0)
  detailedTotalsList = detailedTotalsArray.tolist()
  detailedOutput = os.path.join(options.resultsDir,
                                "optimizationBestResults.csv")
  with open(detailedOutput, 'w') as outFile:

    writer = csv.writer(outFile)
    writer.writerows(detailedResults)
    totalsRow = ['Totals']
    totalsRow.extend(detailedTotalsList)
    writer.writerow(totalsRow)

  # Write out summary results
  outputFile = os.path.join(options.resultsDir, "optimizationSummary.csv")
  with open(outputFile, 'w') as outFile:

    writer = csv.writer(outFile)
    writer.writerows(resultsSummary)
    totalsRow = ['Totals']
    totalsRow.extend(totalsList)
    writer.writerow(totalsRow)

  # Console output
  print "#" * 70
  print "YOUR RESULTS"
  print "Detector: ", detector

  print "Minimum cost:",
  print lowestCost

  print "Best thresholds:"
  for thresh in bestThresholds:
    print "\t" + str(thresh)

  print "Summary file for all thresholds:", outputFile
  print "Detailed summary file for the best threshold:", detailedOutput


def genConfusionMatrix(results,
                       threshold = 0.99,
                       window = 30,
                       windowStepSize = 5,
                       costMatrix = None,
                       verbosity = 0):
  """
  Returns a confusion matrix object for the results of the
  given experiment and the ground truth labels.
  
    experiment      - an experiment info dict
    threshold       - float - cutoff to be applied to Likelihood scores
    window          - Use a WindowedConfusionMatrix and calculate stats over
                      this many minutes.
    windowStepSize  - The ratio of minutes to records
  """
  
  labelName = 'label'
  columnNames = results.columns.tolist()
  if labelName not in columnNames:
    print columnNames
    raise Exception('No labels found. Expected a '
                    'column named "%s"' % labelName)
  
  # If likelihood is equal or above threshold, label it an anomaly, otherwise
  # not
  score = 'anomaly_score'
  predicted = results[score].apply(lambda x: 1 if x >= threshold else 0)
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
                 window = 30,
                 costMatrix = None,
                 verbosity = 0):
  """
  Returns a dict containing lists of data for plotting
  
  experiment  - expInfo dict
  minThresh   - Where to start our threshold search
  maxThresh   - Where to stop the threshold search (inclusive)
  step        - The increment size between each threshold test. This will be
                varied during the run to increase resolution near 1.0.
  """
  
  vals = {'tprs': [],
           'fprs': [],
           'thresholds': [],
           'costs': []}

  incrementCount = 1.0
  while minThresh < maxThresh and incrementCount < 60:
    cMatrix = genConfusionMatrix(results,
                                 minThresh,
                                 window = window,
                                 costMatrix = costMatrix,
                                 verbosity = verbosity)
    vals['tprs'].append(cMatrix.tpr)
    vals['fprs'].append(cMatrix.fpr)
    vals['thresholds'].append(minThresh)
    vals['costs'].append(cMatrix.cost)

    minThresh, step = updateThreshold(minThresh, step, incrementCount)
    incrementCount += 1.0

  
  return vals

def plotROC(py, curveData, chartTitle = "ROC Curve"):
  """
  Returns a URL to a plot of an ROC curve for the given data.
  
    py        - Connection to Plotly
    curveData - dict - Must contain a list of true positive rates and
                       false positive rates.
  """
    
  # Default layout
  layout = Layout(title=chartTitle,
                  xaxis=XAxis(title="False Positive Rate",
                              range=[0,1]),
                  yaxis=YAxis(title="True Positive Rate",
                              type="linear",
                              range=[0,1]),
                  showlegend=False
            )
  
  # PLOT THAT STUFF!
  rocTrace = Trace(x=curveData['fprs'],
                   y=curveData['tprs'])

  data = Data([rocTrace])

  fig = Figure(data=data, layout=layout)

  plot_url = py.plot(fig, filename="ROC Curve")
  
  return plot_url

def updateThreshold(thresh, step, incrementCount):
  """
  One method of updating our threshold to generate the ROC curve. Here as soon
  as we reach .9 we begin decreasing the threshold increment in a logarithmic
  fashion, asymptotically approaching 1
  """
  thresh += step
  # Decrease step as we approach 1
  if incrementCount % 9 == 0:
    step /= 10.0

  return thresh, step

def getCostMatrix(config):
  """
  Returns costs associated with each box in a confusion Matrix
  """
  
  return config['CostMatrix']

if __name__ == '__main__':
  # All the command line options
  parser = OptionParser(helpString)
  parser.add_option("-d", "--resultsDir",
                    help="Path to results files. Single detector only!")
  parser.add_option("--plot", default=False, action="store_true",
                    help="Use the Plot.ly library to generate plots")
  parser.add_option("--verbosity", default=0, help="Increase the amount and "
                    "detail of output by setting this greater than 0.")
  parser.add_option("--config", default="benchmark_config.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  options, args = parser.parse_args()
  
  # Main
  optimizeThreshold(options)