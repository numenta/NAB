import csv
import os
import sys
import dateutil
import datetime

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
        if (i % 500) == 0: 
          print ".",
          sys.stdout.flush()

    print "\n"
    print "Completed processing", i, "records at", datetime.datetime.now()
    print "Anomaly scores for", self.inputFile,
    print "have been written to", self.outputFile
