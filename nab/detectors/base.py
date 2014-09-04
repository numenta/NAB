import os
import sys
import math
import pandas
import datetime
from nab.lib.util import makeDirsExist

class AnomalyDetector(object):
  """
  Base class for all anomaly detectors. When inheriting from this class please
  take note of which methods MUST be overridden, as documented below.
  """

  def __init__( self,
                relativePath,
                dataSet,
                labels,
                name,
                probationaryPercent,
                outputDir):

    self.relativePath = relativePath
    self.dataSet = dataSet
    self.labels = labels
    self.name = name
    self.probationaryPeriod =
                        math.floor(probationaryPercent * dataSet.data.shape[0])
    self.outputDir = outputDir
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
    """
    """
    calcMin = probationaryPeriodData.min()
    calcMax = probationaryPeriodData.max()
    calcRange = abs(calcMax - calcMin)
    calcPad = calcRange * .2

    self.inputMin = calcMin - calcPad
    self.inputMax = calcMax + calcPad
    self.configureDetector(probationaryPeriodData)


  def handleRecord(self, inputData):
    """
    Returns a list [anomalyScore, *]. It is required that the first
    element of the list is the anomalyScore. The other elements may
    be anything, but should correspond to the names returned by
    getAdditionalHeaders().

    This method MUST be overridden by subclasses
    """
    pass

  def getOutputPathAndHeader(self):
    """
    todo:
    """
    relativeDir, fileName = os.path.split(self.relativePath)

    fileName =  self.name + "_" + fileName
    outputDir = os.path.join(self.outputDir, self.name, relativeDir)
    makeDirsExist(outputDir)
    outputPath = os.path.join(outputDir, fileName)

    headers = ["timestamp",
                "value",
                "label",
                "anomaly_score"]

    headers.extend(self.getAdditionalHeaders())

    headers.append("alerts")

    return outputPath, headers

  def run(self):
    """
    todo:
    """
    self.configure(self.dataSet.data["value"].loc[:self.probationaryPeriod])

    outputPath, headers = self.getOutputPathAndHeader()

    ans = pandas.DataFrame(columns=headers)
    # print "for loop: %d", id(self)
    for i, row in self.dataSet.data.iterrows():
      # print "beginning label %s: %d\n"% (str(self.labels), id(self))
      # print "label: %d\n"% (id(self))

      label = self.labels["label"][i]

      # print "row to inputData: %d", id(self)
      inputData = row.to_dict()

      # print "handleRecord call: %d", id(self)
      detectorValues = self.handleRecord(inputData)

      # print "thresholdedValues: %d", id(self)
      thresholdedValues = 1 if detectorValues[0] >= self.threshold else 0

      # print "outputrow: %d", id(self)
      outputRow = list(row) + [label] + detectorValues + [thresholdedValues]

      ans.loc[i] = outputRow

      # Progress report
      if (i % 1000) == 0:
        print ".",
        sys.stdout.flush()

    # print "writing to file(%s): %d" % (outputPath, id(self))
    ans.to_csv(outputPath, index=False)

    print "\nCompleted processing", i, "records at", datetime.datetime.now()
    print "Results for", self.dataSet.fileName,
    print "have been written to %s" %(outputPath)
