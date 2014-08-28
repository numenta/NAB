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
find the point on that ROC curve which minimizes the average cost over
multiple user profiles. """

import os
import pandas
import numpy
import csv

from helpers import (sharedSetup,
                     getCSVFiles,
                     getDetailedResults,
                     genConfusionMatrix)

def optimizeThreshold(options):
  """
  Generate ROC curve and find optimum point given cost matrix. Results of
  this analysis will be put into a best and a summary results file.
  """

  # Setup
  config, profiles, dataGroupDirs, detector = sharedSetup(options)

  # Files to loop over
  csvFiles = getCSVFiles(dataGroupDirs, "raw")

  # Thresholds
  threshMin = 0.0
  threshMax = 1.0
  initialThreshStep = .1

  # Accumulate results
  header = None
  resultsSummary = []

  # Loop over all specified results files
  for resultsFile in csvFiles:

    print "Analyzing results file %s ..." % resultsFile
    with open(resultsFile, "r") as fh:
      results = pandas.read_csv(fh)

    for profileName, profile in profiles.iteritems():

      costMatrix = profile["CostMatrix"]
      vals = genCurveData(results,
                          threshMin,
                          threshMax,
                          initialThreshStep,
                          profile["ScoringWindow"],
                          costMatrix,
                          options.verbosity)

      # First time through write out the headers
      if not header:
        header = ["Name", "User Profile"]
        thresholds = vals["thresholds"]
        header.extend(thresholds)
        resultsSummary.append(header)

      # Add a row for each file processed
      resultRow = [resultsFile, profileName]
      resultRow.extend(vals["costs"])
      resultsSummary.append(resultRow)

      costs = vals["costs"]
      costsArray = numpy.array(costs)

  # Sum all values
  resultsSummaryArray = numpy.array(resultsSummary)

  # Skip first row and two columns
  summaryView = resultsSummaryArray[1:,2:].astype("float")

  # Summarize data for file writing
  totalsArray = numpy.sum(summaryView, axis=0)
  totalsList = totalsArray.tolist()
  lowestCost = totalsArray.min()
  minSummaryCostIndices = numpy.where(totalsArray == lowestCost)[0].tolist()
  bestThresholds = [thresholds[ind] for ind in minSummaryCostIndices]

  # Re-run all files with lowest "best" threshold
  minThresh = bestThresholds[0]

  csvType = "raw"
  detailedResults = getDetailedResults(csvType, csvFiles, profiles)
  costIndex = detailedResults[0].index("Cost")

  # Write out detailed results
  detailedResultsArray = numpy.array(detailedResults)

  # Skip first row and two columns
  detailedView = detailedResultsArray[1:,2:].astype("float")

  # Summarize data for file writing
  detailedTotalsArray = numpy.sum(detailedView, axis=0)
  detailedTotalsList = detailedTotalsArray.tolist()
  detailedOutput = os.path.join(options.resultsDir,
                                "optimizationBestResults.csv")
  with open(detailedOutput, "w") as outFile:

    writer = csv.writer(outFile)
    writer.writerows(detailedResults)
    totalsRow = ["Totals", ""]
    totalsRow.extend(detailedTotalsList)
    writer.writerow(totalsRow)

  # Write out summary results
  outputFile = os.path.join(options.resultsDir, "optimizationSummary.csv")
  with open(outputFile, "w") as outFile:

    writer = csv.writer(outFile)
    writer.writerows(resultsSummary)
    totalsRow = ["Totals", ""]
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

def genCurveData(results,
                 minThresh = 0.0,
                 maxThresh = 1.0,
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

  vals = {"tprs": [],
           "fprs": [],
           "thresholds": [],
           "costs": []}

  incrementCount = 1.0
  while minThresh < maxThresh and incrementCount < 60:
    cMatrix = genConfusionMatrix(results,
                                 "anomaly_score",
                                 "label",
                                 window,
                                 5,
                                 costMatrix,
                                 threshold = minThresh,
                                 verbosity = verbosity)


    vals["tprs"].append(cMatrix.tpr)
    vals["fprs"].append(cMatrix.fpr)
    vals["thresholds"].append(minThresh)
    vals["costs"].append(cMatrix.cost)

    minThresh, step = updateThreshold(minThresh, step, incrementCount)
    incrementCount += 1.0

  return vals

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


if __name__ == "__main__":
  # All the command line options
  parser = OptionParser(helpString)
  parser.add_option("-d", "--resultsDir",
                    help="Path to results files. Single detector only!")
  parser.add_option("--verbosity", default=0, help="Increase the amount and "
                    "detail of output by setting this greater than 0.")
  parser.add_option("--config", default="benchmark_config.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")
  parser.add_option("--profiles", default="user_profiles.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  options, args = parser.parse_args()

  # Main
  optimizeThreshold(options)