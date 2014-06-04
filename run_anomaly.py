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

import os
import sys
import csv
import datetime
import dateutil.parser
import simplejson as json

from optparse import OptionParser
from pandas.io.parsers import read_csv
from nupic.frameworks.opf.modelfactory import ModelFactory

import anomaly_likelihood
from skyline.algorithms import (median_absolute_deviation,
                                first_hour_average,
                                stddev_from_average,
                                stddev_from_moving_average,
                                mean_subtraction_cumulation,
                                least_squares,
                                histogram_bins)

def runAnomaly(options):
  """
  Run selected detector on selected file
  """

  outputDir = getOutputDir(options)

  if options.detector == "cla":

    # If not set explicitly, calculate basic statistics up front
    statsWindow = 24 * 12
    with open(options.inputFile) as fh:
      dataFrame = read_csv(fh);

    if options.min == None:
      inputMin = dataFrame.value[:statsWindow].min()
    else:
      inputMin = options.min

    if options.max == None:
      inputMax = dataFrame.value[:statsWindow].max()
    else:
      inputMax = options.max

    # Catch the case where the file only has one value early on.
    if inputMax == inputMin:
      inputMax += 1


    claDetector = CLADetector(inputMin,
                              inputMax,
                              options.inputFile,
                              outputDir)
    claDetector.run()

  elif options.detector == "skyline":
    # How many records to wait before generating results
    probationaryPeriod = 600

    etsyDetector = EtsySkylineDetector(probationaryPeriod,
                                       options.inputFile,
                                       outputDir)
    etsyDetector.run()

  else:
    raise Exception("'%s' is not a recognized detector type." %
                    options.detector)

def getOutputDir(options):
  """
  Return the directory into which we should place results file based on
  input options.

  This will also *create* that directory if it does not already exist.
  """

  base = options.outputDir
  detectorDir = options.detector
  if options.inputFile:
    dataGroupDir = os_path_split_asunder(options.inputFile)[1]
  else:
    dataGroupDir = options.dataGroup
  outputDir = os.path.join(base, detectorDir, dataGroupDir)

  if not os.path.exists(outputDir):
    # This is being run in parralel so watch out for race condition.
    try:
      os.makedirs(outputDir)
    except OSError:
      pass

  return outputDir

def os_path_split_asunder(path, debug=False):
  """
  From http://stackoverflow.com/questions/4579908/cross-platform-splitting-of-path-in-python
  """
  parts = []
  while True:
      newpath, tail = os.path.split(path)
      if debug: print repr(path), (newpath, tail)
      if newpath == path:
          assert not tail
          if path: parts.append(path)
          break
      parts.append(tail)
      path = newpath
  parts.reverse()
  return parts


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
               outputDir):
    """
    inputFile - Path to the csv containing your timeseries data
    outputDir - Path to the directory into which results files should be placed.
    """

    self.inputFile = inputFile

    # Create path to results
    self.inputFilename = os.path.basename(self.inputFile)
    self.outputFilename = self.getOutputPrefix() + "_anomaly_scores_" + \
                            self.inputFilename
    self.outputFile = os.path.join(outputDir,
                              self.outputFilename)

  def getOutputPrefix(self):
    """
    Returns a string to use as a prefix to output file names.

    This method must be overridden by subclasses.
    """

    return ""

  def getAdditionalHeaders(self):
    """
    Returns a list of strings. Subclasses can add in additional columns per 
    record. 

    This method must be overridden to provide the names for those
    columns.
    """

    return []
    
  def handleRecord(inputData):
    """
    Returns a list [anomalyScore, *]. It is required that the first
    element of the list is the anomalyScore. The other elements may
    be anything, but should correspond to the names returned by
    getAdditionalHeaders(). 

    This method must be overridden by subclasses
    """
    pass

  def run(self):
    
    # Run input
    with open (self.inputFile) as fin:
      
      # Open file and setup headers
      reader = csv.reader(fin)
      csvWriter = csv.writer(open(self.outputFile, "wb"))
      outputHeaders = ["timestamp",
                        "value",
                        "label",
                        "anomaly_score"]

      # Add in any additional headers
      outputHeaders.extend(self.getAdditionalHeaders())
      csvWriter.writerow(outputHeaders)
      headers = reader.next()
      
      # Iterate through each record in the CSV file
      print "Starting processing at", datetime.datetime.now()
      for i, record in enumerate(reader, start=1):
        
        # Read the data and convert to a dict
        inputData = dict(zip(headers, record))
        inputData["value"] = float(inputData["value"])
        inputData["timestamp"] = dateutil.parser.parse(inputData["timestamp"])
              
        # Retrieve the detector output and write it to a file
        outputRow = [inputData["timestamp"],
                     inputData["value"],
                     inputData["label"]]
        detectorValues = self.handleRecord(inputData)
        outputRow.extend(detectorValues)
        csvWriter.writerow(outputRow)
        
        # Progress report
        if (i % 500) == 0: print i, "records processed"

    print "Completed processing", i, "records at", datetime.datetime.now()
    print "Anomaly scores for", self.inputFile,
    print "have been written to", self.outputFile

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
    return "cla"

  def getAdditionalHeaders(self):
    """
    Returns a list of strings.
    """

    return ["_raw_score"]

  def handleRecord(self, inputData):
    """
    Returns a list [anomalyScore, rawScore].

    Internally to NuPIC "anomalyScore" corresponds to "likelihood_score"
    and "rawScore" corresponds to "anomaly_score". Sorry about that.
    """

    # Send it to the CLA and get back the results
    result = self.model.run(inputData)
    
    # Retrieve the anomaly score and write it to a file
    rawScore = result.inferences['anomalyScore']

    # Compute the Anomaly Likelihood
    anomalyScore = self.anomalyLikelihood.likelihood(inputData["value"],
                                                     rawScore,
                                                     inputData["timestamp"])

    return [anomalyScore, rawScore]

#############################################################################

class EtsySkylineDetector(AnomalyDetector):

  def __init__(self, probationaryPeriod, *args, **kwargs):
    
    # Store our running history
    self.timeseries = []
    self.recordCount = 0
    self.probationaryPeriod = probationaryPeriod

    self.algorithms =    [median_absolute_deviation,
                         first_hour_average,
                         stddev_from_average,
                         stddev_from_moving_average,
                         mean_subtraction_cumulation,
                         least_squares,
                         histogram_bins]


    super(EtsySkylineDetector, self).__init__(*args, **kwargs)

  def getOutputPrefix(self):
    return "skyline"

  def handleRecord(self, inputData):
    """
    Returns a list [anomalyScore].
    """

    score = 0.0
    inputRow = [inputData["timestamp"], inputData["value"]]
    self.timeseries.append(inputRow)
    if self.recordCount < self.probationaryPeriod:
      self.recordCount += 1
    else:
      for algo in self.algorithms:
        score += algo(self.timeseries)

    normalizedScore = score / len(self.algorithms)
    return [normalizedScore]


if __name__ == "__main__":
  helpString = (
    "\n%prog [options] [uid]"
    "\n%prog --help"
    "\n"
    "\nRuns NuPIC anomaly detection on a csv file."
    "\nWe assume the data files have a timestamp field called 'timestamp' and"
    "\na value field called 'value'. All other fields are ignored."
    "\nNote: it is important to set min and max properly according to data."
  )

  resultsPathDefault = os.path.join("results", "anomaly_scores.csv");

  # All the command line options
  parser = OptionParser(helpString)
  parser.add_option("--inputFile",
                    help="Path to data file. (default: %default)", 
                    dest="inputFile", default=None)
  parser.add_option("--outputDir",
                    help="Output Directory. Results files will be place here.",
                    dest="outputDir", default="results")
  parser.add_option("--max", default=None,
      help="Maximum number for the value field. If not set this value will be "
          "calculated from the inputFile data.")
  parser.add_option("--min", default=None,
      help="Minimum number for the value field. If not set this value will be "
          "calculated from the inputFile data.")
  parser.add_option("--verbosity", default=0, help="Increase the amount and "
                    "detail of output by setting this greater than 0.")
  parser.add_option("--plot", default=False, action="store_true",
                    help="Use the Plot.ly library to generate plots")
  parser.add_option("--detector", help="Which Anomaly Detector class to use.",
                    default="cla")
  parser.add_option("--dataGroup", help="Which data group to run.")


  options, args = parser.parse_args(sys.argv[1:])

  # Run it
  runAnomaly(options)



