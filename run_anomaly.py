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

"""
A simple client to run CLA anomaly detection using the OPF.
"""

import os
import sys
import csv
import datetime
import dateutil.parser

from optparse import OptionParser
from random import uniform

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.predictionmetricsmanager import MetricsManager

import model_params
import anomaly_likelihood

def createModel():
  return ModelFactory.create(model_params.MODEL_PARAMS)


def runAnomaly(options):
  """
  Create and run a CLA Model on the given dataset (based on the hotgym anomaly
  client in NuPIC).
  """
  
  # Update the min/max value for the encoder
  sensorParams = model_params.MODEL_PARAMS['modelParams']['sensorParams']
  sensorParams['encoders']['value']['maxval'] = options.max
  sensorParams['encoders']['value']['minval'] = options.min
  
  model = createModel()
  model.enableInference({'predictedField': 'value'})
  
  # Create path to results
  inputFilename = os.path.basename(options.inputFile)
  if not options.outputFile:
    outputFile = "anomaly_scores_" + inputFilename
  else:
    outputFile = options.outputFile
  outputPath = os.path.join(options.outputDir,
                            outputFile)
  
  
  # Run input
  with open (options.inputFile) as fin:
    
    # Open file and setup headers
    reader = csv.reader(fin)
    csvWriter = csv.writer(open(outputPath,"wb"))
    csvWriter.writerow(["timestamp",
                        "value",
                        "anomaly_score",
                        "likelihood_score",
                        "label"])
    headers = reader.next()
    
    # Iterate through each record in the CSV file
    print "Starting processing at",datetime.datetime.now()
    for i, record in enumerate(reader, start=1):
      
      # Read the data and convert to a dict
      inputData = dict(zip(headers, record))
      inputData["value"] = float(inputData["value"])
      inputData["dttm"] = dateutil.parser.parse(inputData["dttm"])
      
      # Send it to the CLA and get back the results
      result = model.run(inputData)
      
      # Retrieve the anomaly score and write it to a file
      anomalyScore = result.inferences['anomalyScore']
      # TOTALLY FAKE - TODO Remove!
      likelihoodScore = uniform(0,1)
      csvWriter.writerow([inputData["dttm"],
                          inputData["value"],
                          anomalyScore,
                          likelihoodScore,
                          inputData["label"]])
      
      # Progress report
      if (i%500) == 0: print i,"records processed"

  print "Completed processing",i,"records at", datetime.datetime.now()
  print "Anomaly scores for", options.inputFile,
  print "have been written to", outputPath


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
  runAnomaly(options)



