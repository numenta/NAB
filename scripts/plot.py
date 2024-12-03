# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
"""
This file contains plotting tools for NAB data and results. Run this script to
generate example plots.
"""

from nab.plot import PlotNAB



if __name__ == "__main__":

  # To use this script modify one of the code samples below.

  # Sample 1: shows how to plot a set of raw data files with their labels.
  # You can optionally show the windows or probationary period.

  dataFiles = (
      "realKnownCause/machine_temperature_system_failure.csv",
      "realAWSCloudwatch/ec2_cpu_utilization_fe7f93.csv")
  dataNames = (
      "Machine Temperature Sensor Data",
      "AWS Cloudwatch CPU Utilization Data")

  assert len(dataFiles) == len(dataNames)

  for i in range(len(dataFiles)):
    dataPlotter = PlotNAB(
        dataFile=dataFiles[i],
        dataName=dataNames[i],
        offline=True,
    )
    dataPlotter.plot(
        withLabels=True,
        withWindows=False,
        withProbation=False)


  # Sample 2: to plot the results of running one or more detectors uncomment
  # the following and update the list of dataFiles, dataNames, and detectors.
  # Note that you must have run every detector on each data file. You can
  # optionally show the point labels, windows or probationary period. You can
  # also use one of the non-standard profiles.

  # dataFiles = (
  #     "realKnownCause/machine_temperature_system_failure.csv",
  #     "realKnownCause/ambient_temperature_system_failure.csv"
  # )
  # dataNames = (
  #     "Machine Temperature Sensor Data",
  #     "Ambient Temperature System Failure Data"
  # )
  # detectors=["numenta", "null"]
  
  # assert len(dataFiles) == len(dataNames)
  
  # # Create the list of result filenames for each detector
  # allResultsFiles = []
  # for f in dataFiles:
  #   resultFiles = []
  #   for d in detectors:
  #     filename = d + "/"+f.replace("/","/"+d+"_")
  #     resultFiles.append(filename)
  #   allResultsFiles.append(resultFiles)
  
  # # Now plot everything
  # for i in range(len(dataFiles)):
  #   dataPlotter = PlotNAB(
  #       dataFile=dataFiles[i],
  #       dataName=dataNames[i],
  #       offline=True)
  #   dataPlotter.plotMultipleDetectors(
  #       allResultsFiles[i],
  #       detectors=detectors,
  #       scoreProfile="standard",
  #       withLabels=False,
  #       withWindows=True,
  #       withProbation=True)
