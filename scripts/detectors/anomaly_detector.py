import csv
import os
import sys
import dateutil
import datetime
import multiprocessing
from copy import copy
from pandas.io.parsers import read_csv

def makeDirsExist(path):
    """
    Makes sure a given path exists
    """

    if not os.path.exists(path):
      # This is being run in parralel so watch out for race condition.
      try:
        os.makedirs(path)
      except OSError:
        pass


class AnomalyDetector(object):
  """
  Base class for all anomaly detectors. When inheriting from this class please
  take note of which methods MUST be overridden, as documented below.
  """

  def __init__(self,
              corpus,
              labels,
              name,
              probationaryPercent,
              outputDir,
              numCPUs):
    self.corpus = corpus
    self.labels = labels
    self.probationaryPercent = probationaryPercent
    self.outputDir = outputDir
    self.numCPUs = numCPUs
    self.threshold = self.getThreshold()


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

  def ConfigureDetector(self, probationaryPeriodData):
    """
    Takes the probationary period data and is allowed to do any statistical
    calculation with it in order to configure itself
    """

  def setThreshold(self):
    if self.threshold:
      return self.threshold
    print 'Error: No threshold set'
    sys.exit()


  def handleRecord(self, inputData):
    """
    Returns a list [anomalyScore, *]. It is required that the first
    element of the list is the anomalyScore. The other elements may
    be anything, but should correspond to the names returned by
    getAdditionalHeaders().

    This method MUST be overridden by subclasses
    """
    pass

  def runCorpus(self):
    p = multiprocessing.Pool(self.numCpu)
    for relativePath in self.corpus.dataSets:
      self.runFile(relativePath)

    p.map(self.runFile, self.corpus.dataSets.keys())


  def getWriters(self, filename):
    rawFilename = self.getOutputPrefix() + "_raw_scores_" + filename
    rawOutPath = os.path.join(self.outputDir, 'raw')
    rawOutputFile = os.path.join(rawOutPath, rawFilename)
    makeDirsExist(rawOutPath)
    rawWriter = csv.writer(open(rawOutputFile, "wb"))

    alertFilename = self.getOutputPrefix() + "_alerts_" + filename
    alertOutPath = os.path.join(self.outputDir, 'alerts')
    alertOutputFile = os.path.join(alertOutPath, alertFilename)
    makeDirsExist(alertOutPath)
    alertWriter = csv.writer(open(alertOutputFile, "wb"))

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

    return rawWriter, alertWriter

  def runFile(self, relativePath):
    data = self.corpus.dataSets[relativePath]

    probationaryPeriod = self.probationaryPercent * data.shape[0]

    rawWriter, alertWriter = self.getWriters(data.filename)

    # Iterate through each record in the CSV file
    print "Starting processing at", datetime.datetime.now()
    for i, row in data.iterrows():
      # Retrieve the detector output and write it to a file
      row = list(row) + [self.labels.labels[relativePath][i]]
      detectorValues = self.handleRecord(row)
      thresholdedValues = [1.0] if detectorValues[0] >= self.threshold else [0.0]

      rawOutputRow = copy(row) + [detectorValues]
      alertOutputRow = copy(row) + [thresholdedValues]

      rawWriter.writerow(rawOutputRow)
      alertWriter.writerow(alertOutputRow)

      # Progress report
      if (i % 500) == 0:
        print ".",
        sys.stdout.flush()

    print "\nCompleted processing", i, "records at", datetime.datetime.now()
    print "Alerts for", self.inputFile,
    print "have been written to", self.alertOutputFile
