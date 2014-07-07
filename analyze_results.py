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

helpString = """ This script will evaluate the alert performance of a given 
detector. """

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


def analyzeResults(options):
  """
  Score the output of detectors.
  """

  # Load the config file
  with open(options.config) as configHandle:
    config = yaml.load(configHandle)

  # Update any missing config values from global config file
  if not options.resultsDir:
    options.resultsDir = config["ResultsDirectory"]

  options.detectors = config["AnomalyDetectors"]

  # Find sub directories of our results dir, e.g. results/grok/...
  items = os.listdir(options.resultsDir)
  dataGroupDirs = []
  for item in items:
    path = os.path.join(options.resultsDir, item)
    if os.path.isdir(path):
      for d in options.detectors:
        if d == item: 
          print("ERROR: It looks like you're trying to analyze results from "
                "multiple detectors at once. \nThis script generates results "
                "summaries which are only meaningful on a per-detector basis.\n"
                "Please specify a single detector results directory. e.g. "
                "python analyze_results.py -d results/grok")
          sys.exit(1)
      dataGroupDirs.append(path)

  # Infer which detector generated these results from the path
  detector = inferDetector(options)

  csvFiles = []
  for dataGroupDir in dataGroupDirs:
    alertsDir = os.path.join(dataGroupDir, 'alerts')
    items = os.listdir(alertsDir)
    files = [os.path.join(alertsDir, item) for
                item in items if item[-4:] == '.csv']
    csvFiles.extend(files)

  if not csvFiles:
    print("No files to analyze.")
    sys.exit(0)

  # Analyze all files
  detailedResults = []
  headers = ["Alert Log File",
             "True Positives",
             "False Positives",
             "False Negatives",
             "True Negatives",
             "Cost",
             "Total Normal",
             "Total Anomalous"]

  costIndex = headers.index("Cost")
  detailedResults.append(headers)
  for resultsFile in csvFiles:

    with open(resultsFile, 'r') as fh:
      results = pandas.read_csv(fh)
    
    costMatrix = getCostMatrix(config)
    # TODO - Window should be settable from config
    cMatrix = genConfusionMatrix(results,
                                 window=120,
                                 costMatrix = costMatrix)

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
  detailedOutput = os.path.join(options.resultsDir, "detailedResults.csv")
  with open(detailedOutput, 'w') as outFile:

    writer = csv.writer(outFile)
    writer.writerows(detailedResults)
    totalsRow = ['Totals']
    totalsRow.extend(detailedTotalsList)
    writer.writerow(totalsRow)

  # Load and compare results to leaderboard
  with open("leaderboard.yaml") as fh:
    leaderboard = yaml.load(fh)

  print "#" * 70
  print "LEADERBOARD"
  pprint(leaderboard)

  print "#" * 70
  print "YOUR RESULTS"
  print "Detector: ", detector

  print "Total cost:",
  print totalsRow[costIndex]

  print "Detailed summary file:", detailedOutput

  congrats(totalsRow[costIndex], leaderboard)


def congrats(currentCost, leaderboard):
  """
  Prints a congratulatory note if the measured results are better than
  known values.
  """
  bestKnownCost = leaderboard["FullCorpus"]["Cost"]
  if currentCost < bestKnownCost:
    print "Congratulations! These results improve on the state of the art."
    print "Your minimum cost (%d) is less than the best known value (%d)" % \
           (currentCost, bestKnownCost)


def inferDetector(options):
  """
  Returns a string which is either a known detector name or "Unknown" if 
  the infered detector does not match one we know.
  """

  guess = os.path.split(options.resultsDir)[1]

  if guess in options.detectors:
    return guess
  else:
    return "Unknown"


def genConfusionMatrix(results,
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
  
  alertName = 'alert'
  predicted = results[alertName]
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
  analyzeResults(options)