import csv
import os
import sys
import dateutil
import datetime

from copy import copy
from pandas.io.parsers import read_csv

class AnomalyDetector(object):
  """
  Base class for all anomaly detectors. When inheriting from this class please
  take note of which methods MUST be overridden, as documented below.
  """

  def __init__(self,
               probationaryPeriod,
               inputFile,
               outputDir):
    """
    inputFile - Path to the csv containing your timeseries data
    outputDir - Path to the directory into which results files should be placed.
    """

    self.inputFile = inputFile
    self.probationaryPeriod = probationaryPeriod

    # Allowed statistics. Anything within probationary period.
    with open(self.inputFile) as fh:
      dataFrame = read_csv(fh);

    calcMin = dataFrame.value[:self.probationaryPeriod].min()
    calcMax = dataFrame.value[:self.probationaryPeriod].max()
    calcRange = abs(calcMax - calcMin)
    calcPad = calcRange * .2

    self.inputMin = calcMin - calcPad
    self.inputMax = calcMax + calcPad

    # Define threshold
    self.threshold = self.getThreshold()

    # Catch the case where the file only has one value early on.
    if self.inputMax == self.inputMin:
      self.inputMax += 1

    # Create path to alert files and raw score files
    self.inputFilename = os.path.basename(self.inputFile)
    alertFilename = self.getOutputPrefix() + "_alerts_" + \
                         self.inputFilename
    rawFilename = self.getOutputPrefix() + "_raw_scores_" + \
                                self.inputFilename

    alertOutPath = os.path.join(outputDir, 'alerts')
    rawOutPath = os.path.join(outputDir, 'raw')
    self._makeDirsExist(alertOutPath)
    self._makeDirsExist(rawOutPath)
    self.alertOutputFile = os.path.join(alertOutPath, alertFilename)
    self.rawOutputFile = os.path.join(rawOutPath, rawFilename)

  def getOutputPrefix(self):
    """
    Returns a string to use as a prefix to output file names.

    This method MUST be overridden by subclasses.
    """

    return ""

  def getAdditionalHeaders(self):
    """
    Returns a list of strings. Subclasses can add in additional columns per 
    record. 

    This method MAY be overridden to provide the names for those
    columns.
    """

    return []

  def getThreshold(self):
    """
    Returns a float between 0.0 and 1.0. This will be used to decide if a given
    record becomes an alert.

    This method MUST be overridden by child classes.
    """
    pass
    
  def handleRecord(inputData):
    """
    Returns a list [anomalyScore, *]. It is required that the first
    element of the list is the anomalyScore. The other elements may
    be anything, but should correspond to the names returned by
    getAdditionalHeaders(). 

    This method MUST be overridden by subclasses
    """
    pass

  def _makeDirsExist(self, path):
    """
    Makes sure a given path exists
    """

    if not os.path.exists(path):
      # This is being run in parralel so watch out for race condition.
      try:
        os.makedirs(path)
      except OSError:
        pass

  def run(self):
    
    # Run input
    with open (self.inputFile) as fin:
      
      # Open files and setup headers
      reader = csv.reader(fin)
      alertWriter = csv.writer(open(self.alertOutputFile, "wb"))
      rawWriter = csv.writer(open(self.rawOutputFile, "wb"))
      headers = ["timestamp",
                  "value",
                  "label"]

      alertHeaders = copy(headers)
      alertHeaders.append("alert")
      rawHeaders = copy(headers)
      rawHeaders.append("anomaly_score")

      # Add in any additional headers (if any)
      alertWriter.writerow(alertHeaders)
      rawHeaders.extend(self.getAdditionalHeaders())
      rawWriter.writerow(rawHeaders)

      # Process the input files
      inHeaders = reader.next()
      
      # Iterate through each record in the CSV file
      print "Starting processing at", datetime.datetime.now()
      for i, record in enumerate(reader, start=1):
        
        # Read the data and convert to a dict
        inputData = dict(zip(inHeaders, record))
        inputData["value"] = float(inputData["value"])
        inputData["timestamp"] = dateutil.parser.parse(inputData["timestamp"])
              
        # Retrieve the detector output and write it to a file
        outputRow = [inputData["timestamp"],
                     inputData["value"],
                     inputData["label"]]
        detectorValues = self.handleRecord(inputData)
        rawOutputRow = copy(outputRow)
        rawOutputRow.extend(detectorValues)
        rawWriter.writerow(rawOutputRow)

        thresholdedValues = [1.0] if detectorValues[0] >= self.threshold else [0.0]
        alertOutputRow = copy(outputRow)
        alertOutputRow.extend(thresholdedValues)
        alertWriter.writerow(alertOutputRow)
        
        # Progress report
        if (i % 500) == 0: 
          print ".",
          sys.stdout.flush()

    print "\n"
    print "Completed processing", i, "records at", datetime.datetime.now()
    print "Alerts for", self.inputFile,
    print "have been written to", self.alertOutputFile
