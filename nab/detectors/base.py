import os
import sys
import math
import pandas
from nab.lib.util import makeDirsExist

class AnomalyDetector(object):
  """
  Base class for all anomaly detectors. When inheriting from this class please
  take note of which methods MUST be overridden, as documented below.
  """

  def __init__( self,
                dataSet,
                probationaryPercent):

    self.dataSet = dataSet
    self.probationaryPeriod = \
                        math.floor(probationaryPercent * dataSet.data.shape[0])
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
    This functions takes the probationary period data and calculates some
    """
    self.inputMin = probationaryPeriodData.min()
    self.inputMax = probationaryPeriodData.max()
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

  def getHeader(self):
    """
    Gets the outputPath and all the headers needed to write the results files.
    """
    headers = ["timestamp",
                "value",
                "anomaly_score"]

    headers.extend(self.getAdditionalHeaders())

    headers.append("alerts")

    return headers

  def run(self):
    """
    Main function that is called to collect anomaly scores for a given file.
    """
    self.configure(self.dataSet.data["value"].loc[:self.probationaryPeriod])

    headers = self.getHeader()

    ans = pandas.DataFrame(columns=headers)
    # print "for loop: %d", id(self)
    for i, row in self.dataSet.data.iterrows():

      # print "row to inputData: %d", id(self)
      inputData = row.to_dict()

      # print "handleRecord call: %d", id(self)
      detectorValues = self.handleRecord(inputData)

      # print "thresholdedValues: %d", id(self)
      thresholdedValue = 1 if detectorValues[0] >= self.threshold else 0

      # print "outputrow: %d", id(self)
      outputRow = list(row) + detectorValues + [thresholdedValue]

      ans.loc[i] = outputRow

      # Progress report
      if (i % 1000) == 0:
        print ".",
        sys.stdout.flush()

    print
    return ans

