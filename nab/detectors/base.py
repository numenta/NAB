import csv
import os
import sys
import math
import datetime
import multiprocessing
from copy import copy

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
              numCPUs,):
    self.corpus = corpus
    self.labels = labels
    self.name = name
    self.probationaryPercent = probationaryPercent
    self.outputDir = os.path.join(outputDir,self.name)
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

  def configureDetector(self, probationaryPeriodData):
    """
    Takes the probationary period data and is allowed to do any statistical
    calculation with it in order to configure itself
    """
    pass

  def configure(self, probationaryPeriodData):
    calcMin = probationaryPeriodData.min()
    calcMax = probationaryPeriodData.max()
    calcRange = abs(calcMax - calcMin)
    calcPad = calcRange * .2

    self.inputMin = calcMin - calcPad
    self.inputMax = calcMax + calcPad
    self.configureDetector(probationaryPeriodData)


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
    # p = multiprocessing.Pool(self.numCPUs)

    for relativePath in self.corpus.dataSets:
      print relativePath
      self.runFile(relativePath)

    # p.map(self.runFile, self.corpus.dataSets.keys())


  def getWriters(self, relativePath, filename):
    relativeDir = os.path.split(relativePath)[0]

    rawFilename = self.getOutputPrefix() + "_raw_scores_" + filename
    rawOutPath = os.path.join(self.outputDir, relativeDir, 'raw')
    rawOutputFile = os.path.join(rawOutPath, rawFilename)
    makeDirsExist(rawOutPath)
    rawWriter = csv.writer(open(rawOutputFile, "wb"))

    alertFilename = self.getOutputPrefix() + "_alerts_" + filename
    alertOutPath = os.path.join(self.outputDir, relativeDir, 'alerts')
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

    return [rawWriter, alertWriter],[rawOutputFile, alertOutputFile]

  def runFile(self, relativePath):
    dataSet = self.corpus.dataSets[relativePath]

    # print 'in detector',
    # print self.probationaryPercent,
    # print dataSet.data.shape[0],
    probationaryPeriod = math.floor(self.probationaryPercent * dataSet.data.shape[0])
    # print probationaryPeriod

    self.configure(dataSet.data['value'].loc[:probationaryPeriod])

    [rawWriter, alertWriter],[rawOutputFile, alertOutputFile] = self.getWriters(relativePath, dataSet.fileName)

    rawWriter

    for i, row in dataSet.data.iterrows():
      # Retrieve the detector output and write it to a file
      # print self.labels.labels[relativePath]['label'][i]
      label = self.labels.labels[relativePath]['label'][i]
      inputData = row.to_dict()

      row = list(row) + [label]

      detectorValues = self.handleRecord(inputData)
      thresholdedValues = [1.0] if detectorValues[0] >= self.threshold else [0.0]

      rawOutputRow = copy(row)
      rawOutputRow.extend(detectorValues)
      alertOutputRow = copy(row)
      alertOutputRow.extend(thresholdedValues)

      rawWriter.writerow(rawOutputRow)
      alertWriter.writerow(alertOutputRow)


      # Progress report
      if (i % 500) == 0:
        print ".",
        sys.stdout.flush()

    print "\nCompleted processing", i, "records at", datetime.datetime.now()
    print "Alerts for", dataSet.fileName,
    print "have been written to %s and %s" %(alertOutputFile, rawOutputFile)
