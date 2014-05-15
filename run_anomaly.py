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

import os
import sys
import csv
import datetime
import dateutil.parser
import simplejson as json

from optparse import OptionParser
from nupic.frameworks.opf.modelfactory import ModelFactory

import anomaly_likelihood


def main(options):
  """
  Runs each of the anomaly detectors in trun
  """

  claDetector = CLADetector(options.min,
                            options.max,
                            options.inputFile,
                            options.outputDir,
                            options.outputFile)
  claDetector.run()

#############################################################################

class AnomalyLikelihood(object):
  """
  Helper class for running anomaly likelihood computation.
  """
  
  def __init__(self, probationaryPeriod = 600, CLALearningPeriod = 300):
    """
    CLALearningPeriod - the number of iterations required for the CLA to
    learn some of the patterns in the dataset.
    
    probationaryPeriod - no anomaly scores are reported for this many
    iterations.  This should be CLALearningPeriod + some number of records
    for getting a decent likelihood estimation.
    
    """
    self._iteration          = 0
    self._historicalScores   = []
    self._distribution       = None
    self._probationaryPeriod = probationaryPeriod
    self._CLALearningPeriod  = CLALearningPeriod


  def _computeLogLikelihood(self, likelihood):
    """
    Compute a log scale representation of the likelihood value. Since the
    likelihood computations return low probabilities that often go into 4 9's or
    5 9's, a log value is more useful for visualization, thresholding, etc.
    """
    # The log formula is:
    # Math.log(1.0000000001 - likelihood) / Math.log(1.0 - 0.9999999999);
    return math.log(1.0000000001 - likelihood) / -23.02585084720009


  def likelihood(self, value, anomalyScore, dttm):
    """
    Given the current metric value, plus the current anomaly
    score, output the anomalyLikelihood for this record.
    """
    dataPoint = (dttm, value, anomalyScore)
    # We ignore the first probationaryPeriod data points
    if len(self._historicalScores) < self._probationaryPeriod:
      likelihood = 0.5
    else:
      # On a rolling basis we re-estimate the distribution every 100 iterations
      if self._distribution is None or (self._iteration % 100 == 0): 
        _, _, self._distribution = (
          anomaly_likelihood.estimateAnomalyLikelihoods(
            self._historicalScores,
            skipRecords = self._CLALearningPeriod)
          )
        
      likelihoods, _, self._distribution = (
        anomaly_likelihood.updateAnomalyLikelihoods([dataPoint],
          self._distribution)
      )
      likelihood = 1.0 - likelihoods[0]
      
    # Before we exit update historical scores and iteration
    self._historicalScores.append(dataPoint)
    self._iteration += 1

    return likelihood

#############################################################################

class AnomalyDetector(object):

  def __init__(self,
               inputFile,
               outputDir,
               outputFilename):
    """
    inputFile - Path to the csv containing your timeseries data
    outputDir - Name of directory to which results files will be written
    outputFilename - Name of file to which results will be written
    """

    self.inputFile = inputFile

    # Create path to results
    self.inputFilename = os.path.basename(self.inputFile)
    if not outputFilename:
      self.outputFilename = self.getOutputPrefix() + self.inputFilename
    else:
      self.outputFilename = outputFilename
    self.outputPath = os.path.join(outputDir,
                              self.outputFilename)

  def getOutputPrefix():
    """
    Returns a string to use as a prefix to output file names.

    This method must be overridden by subclasses.
    """

    return ""
    
  def handleRecord(inputData):
    """
    Returns a tuple (anomalyScore, likelihoodScore). 

    This method must be overridden by subclasses
    """
    pass

  def run(self):
    
    # Run input
    with open (self.inputFile) as fin:
      
      # Open file and setup headers
      reader = csv.reader(fin)
      csvWriter = csv.writer(open(self.outputPath, "wb"))
      csvWriter.writerow(["timestamp",
                          "value",
                          "anomaly_score",
                          "likelihood_score",
                          "label"])
      headers = reader.next()
      
      # Iterate through each record in the CSV file
      print "Starting processing at", datetime.datetime.now()
      for i, record in enumerate(reader, start=1):
        
        # Read the data and convert to a dict
        inputData = dict(zip(headers, record))
        inputData["value"] = float(inputData["value"])
        inputData["dttm"] = dateutil.parser.parse(inputData["dttm"])
              
        # Retrieve the anomaly score and write it to a file
        anomalyScore, likelihoodScore = self.handleRecord(inputData)
        csvWriter.writerow([inputData["dttm"],
                            inputData["value"],
                            anomalyScore,
                            likelihoodScore,
                            inputData["label"]])
        
        # Progress report
        if (i % 500) == 0: print i,"records processed"

    print "Completed processing",i,"records at", datetime.datetime.now()
    print "Anomaly scores for", self.inputFile,
    print "have been written to", self.outputPath

#############################################################################

class CLADetector(AnomalyDetector):

  def __init__(self, minVal, maxVal, *args, **kwargs):

    # Load the model params JSON
    with open("model_params.json") as fp:
      modelParams = json.load(fp)

    # Update the min/max value for the encoder
    self.sensorParams = modelParams['modelParams']['sensorParams']
    self.sensorParams['encoders']['value']['minval'] = minVal
    self.sensorParams['encoders']['value']['maxval'] = maxVal
    
    self.model = ModelFactory.create(modelParams)
    self.model.enableInference({'predictedField': 'value'})

    # The anomaly likelihood object
    self.anomalyLikelihood = AnomalyLikelihood()

    # Init the super class
    super(CLADetector, self).__init__(*args, **kwargs)

  def getOutputPrefix(self):
    """
    Returns the string to prepend to results files generated by this class
    """
    return "cla_anomaly_scores_"

  def handleRecord(self, inputData):
    """
    Returns a tuple (anomalyScore, likelihoodScore).
    """

    # Send it to the CLA and get back the results
    result = self.model.run(inputData)
    
    # Retrieve the anomaly score and write it to a file
    anomalyScore = result.inferences['anomalyScore']

    # Compute the Anomaly Likelihood
    likelihoodScore = self.anomalyLikelihood.likelihood(inputData["value"],
                                                        anomalyScore,
                                                        inputData["dttm"])

    return anomalyScore, likelihoodScore

#############################################################################

class ThresholdDetector(AnomalyDetector):

  def handleRecord(inputData):
    """
    Returns a tuple (anomalyScore, likelihoodScore).
    """

    probationPeriod = 24 * 12
    probationValues = []

    while self.recordsSeen < probationPeriod:
      probationValues.append(float(inputData["value"]))
      self.recordsSeen += 1
      # Return 0s during probation
      return (0.0, 0.0)

if __name__ == "__main__":
  helpString = (
    "\n%prog [options] [uid]"
    "\n%prog --help"
    "\n"
    "\nRuns NuPIC anomaly detection on a csv file."
    "\nWe assume the data files have a timestamp field called 'dttm' and"
    "\na value field called 'value'. All other fields are ignored."
    "\nNote: it is important to set min and max properly according to data."
  )

  resultsPathDefault = os.path.join("results", "anomaly_scores.csv");

  # All the command line options
  parser = OptionParser(helpString)
  parser.add_option("--inputFile",
                    help="Path to data file. (default: %default)", 
                    dest="inputFile", default="data/hotgym.csv")
  parser.add_option("--outputFile",
                    help="Output file. Results will be written to this file."
                    " By default 'anomaly_scores_' will be prepended to the "
                    "input file name.", 
                    dest="outputFile", default = None)
  parser.add_option("--outputDir",
                    help="Output Directory. Results files will be place here.",
                    dest="outputDir", default="results")
  parser.add_option("--max", default=100.0, type=float,
      help="Maximum number for the value field. [default: %default]")
  parser.add_option("--min", default=0.0, type=float,
      help="Minimum number for the value field. [default: %default]")
  
  options, args = parser.parse_args(sys.argv[1:])

  # Run it
  main(options)



