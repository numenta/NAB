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
import math
import pandas
from nab.util import createPath
from datetime import datetime



class AnomalyDetector(object):
  """
  Base class for all anomaly detectors. When inheriting from this class please
  take note of which methods MUST be overridden, as documented below.
  """

  def __init__( self,
                dataSet,
                probationaryPercent):

    self.dataSet = dataSet
    self.probationaryPeriod = math.floor(
      probationaryPercent * dataSet.data.shape[0])
    self.threshold = self.getThreshold()

  def getOutputPrefix(self):
    """Returns a string to use as a prefix to output file names.

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
    This functions takes the probationary period data and calculates some.
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
    for i, row in self.dataSet.data.iterrows():

      inputData = row.to_dict()

      detectorValues = self.handleRecord(inputData)

      thresholdedValue = 1 if detectorValues[0] >= self.threshold else 0

      outputRow = list(row) + list(detectorValues) + [thresholdedValue]

      ans.loc[i] = outputRow

      # Progress report
      if (i % 1000) == 0:
        print ".",
        sys.stdout.flush()

    print
    return ans


def detectDataSet(args):
  """
  Function called in each detector process that run the detector that it is
  given.

  @param args   (tuple)   Arguments to run a detector on a file and then
  """
  (i, detectorInstance, detectorName, labels, outputDir, relativePath) = args

  relativeDir, fileName = os.path.split(relativePath)
  fileName =  detectorName + "_" + fileName
  outputPath = os.path.join(outputDir, detectorName, relativeDir, fileName)
  createPath(outputPath)

  print "%s: Beginning detection with %s for %s" % \
                                                (i, detectorName, relativePath)

  results = detectorInstance.run()

  results["label"] = labels

  results.to_csv(outputPath, index=False, float_format="%.3f")

  print "%s: Completed processing %s records  at %s" % \
                                        (i, len(results.index), datetime.now())
  print "%s: Results have been written to %s" % (i, outputPath)

