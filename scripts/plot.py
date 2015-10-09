# ----------------------------------------------------------------------
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
"""
This file contains plotting tools for NAB data and results. Run this script to
generate example plots.
"""

import itertools
import os
import pandas as pd
import plotly.plotly as py

from plotly.graph_objs import (
    Bar, Data, Figure, Layout, Line, Marker, Scatter, XAxis, YAxis)

try:
  import simplejson as json
except ImportError:
  import json


def getJSONData(jsonPath):
  with open(jsonPath) as f:
    dataDict = json.load(f)
  return dataDict


def getCSVData(dataPath):
  try:
    data = pd.read_csv(dataPath)
  except IOError("Invalid path to data file."):
    return
  return data



class PlotNAB(object):
  """Plot NAB data and results files with the plotly API."""

  def __init__(self,
               apiKey=None,
               username=None,
               dataFile=None,
               dataName=""):

    # Instantiate API credentials.
    try:
      self.apiKey = apiKey if apiKey else os.environ["PLOTLY_API_KEY"]
    except:
      print ("Missing PLOTLY_API_KEY environment variable. If you have a "
        "key, set it with $ export PLOTLY_API_KEY=api_key\n"
        "You can retrieve a key by registering for the Plotly API at "
        "http://www.plot.ly")
      raise OSError("Missing API key.")
    try:
      self.username = username if username else os.environ["PLOTLY_USERNAME"]
    except:
      print ("Missing PLOTLY_USERNAME environment variable. If you have a "
        "username, set it with $ export PLOTLY_USERNAME=username\n"
        "You can sign up for the Plotly API at http://www.plot.ly")
      raise OSError("Missing username.")

    py.sign_in(self.username, self.apiKey)

    self._setupDirectories()
    self._getThresholds()

    # Setup data
    self.dataFile = dataFile
    self.dataName = dataName if dataName else dataFile
    self.dataPath = os.path.join(self.dataDir, dataFile)
    self.rawData = getCSVData(self.dataPath) if self.dataPath else None

    # For open shape markers, append "-open" to strings below:
    self.markers = ["circle", "diamond", "square", "cross", "triangle-up",
                    "hexagon", "triangle-down"]


  def _setupDirectories(self):
    root = os.path.dirname(os.path.realpath(__file__))
    self.configDir = os.path.abspath(os.path.join(root, "..", "config"))
    self.dataDir = os.path.abspath(os.path.join(root, "..", "data"))
    self.labelsDir = os.path.abspath(os.path.join(root, "..", "labels"))
    self.resultsDir = os.path.abspath(os.path.join(root, "..", "results"))


  def _getThresholds(self):
    thresholdsPath = os.path.join(self.configDir, "thresholds.json")
    with open(thresholdsPath) as f:
      self.thresholds = json.load(f)


  def _addValues(self):
    """Return data values trace."""
    return Scatter(x=self.rawData["timestamp"],
                   y=self.rawData["value"],
                   name="Value",
                   line=Line(
                     width=1.5
                   ),
                   showlegend=False)


  def _addLabels(self):
    """Return plotly trace for anomaly labels."""
    labels = getJSONData(
      os.path.join(self.labelsDir, "combined_labels.json"))[self.dataFile]

    x = []
    y = []
    for label in labels:
      row = self.rawData[self.rawData.timestamp == label]
      x.append(row["timestamp"])
      y.append(row["value"])

    return Scatter(x=x,
                   y=y,
                   mode="markers",
                   name="Ground Truth Anomaly",
                   text=["anomalous instance"],
                   marker=Marker(
                     color="rgb(200, 20, 20)",
                     size=10.0,
                     symbol=self.markers[0]
                   ))


  def _addWindows(self):
    """Return plotly trace for anomaly windows."""
    windows = getJSONData(
      os.path.join(self.labelsDir, "combined_windows.json"))[self.dataFile]

    x = []
    delta = (pd.to_datetime(self.rawData["timestamp"].iloc[1]) -
             pd.to_datetime(self.rawData["timestamp"].iloc[0]))
    minutes = int(delta.total_seconds() / 60)
    for window in windows:
      start = pd.to_datetime(window[0])
      end = pd.to_datetime(window[1])
      x.append(pd.date_range(start, end, freq=str(minutes) + "Min").tolist())

    x = list(itertools.chain.from_iterable(x))
    y = [self.rawData.value.max() for _ in x]

    return Bar(x=x,
               y=y,
               name="Anomaly Window",
               marker=Marker(
                 color="rgb(220, 100, 100)"
               ),
               opacity=0.3)


  def _addProbation(self):
    # Probationary period trace.
    length = min(int(0.15 * len(self.rawData)), 750)
    x = self.rawData["timestamp"].iloc[:length]
    y = [self.rawData.value.max() for _ in x]

    return Bar(x=x,
               y=y,
               name="Probationary Period",
               marker=Marker(
                 color="rgb(0, 0, 200)"
               ),
               opacity=0.2)


  @staticmethod
  def _createLayout(title):
    """Return plotly Layout object."""
    return Layout(title=title,
                  showlegend=False,
                  width=1000,
                  height=600,
                  xaxis=XAxis(
                    title="Date"
                  ),
                  yaxis=YAxis(
                    title="Metric",
                    domain=[0, 1],
                    autorange=True,
                    autotick=True
                  ),
                  barmode="stack",
                  bargap=0)


  def setDataFile(self, filename):
    """Set the data file name; i.e. path from self.dataDir."""
    self.dataFile = filename


  def setDataName(self, name):
    """Set the name of this data; prints to plot title."""
    self.dataName = name


  def getDataInfo(self):
    """Return member variables dataFile, dataName, and dataPath."""

    return {"dataFile": self.dataFile,
            "dataName": self.dataName,
            "dataPath": self.dataPath}


  def plotRawData(self,
                  withLabels=False,
                  withWindows=False,
                  withProbation=False):
    """Plot the data stream."""

    if self.rawData is None:
      self.rawData = getCSVData(self.dataPath)

    traces = []

    traces.append(self._addValues())

    if withLabels:
      traces.append(self._addLabels())

    if withWindows:
      traces.append(self._addWindows())

    if withProbation:
      traces.append(self._addProbation())

    # Create plotly Data and Layout objects:
    data = Data(traces)
    layout = self._createLayout(self.dataName)

    # Query plotly
    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig)
    print "Data plot URL: ", plot_url

    return plot_url


  def plotMultipleDetectors(self,
                            resultsPaths,
                            detectors=["numenta"],
                            scoreProfile="standard",
                            withLabels=True,
                            withWindows=True,
                            withProbation=True):
    """
    Plot detector results on a data file.

    TODO: auto-generate paths from dataFile and detectors.
    """

    if scoreProfile is (not "standard"
                    or not "reward_low_fn_rate"
                    or not "reward_low_fp_rate"):
      raise ValueError("Invalid scoring profile. Must be one of \'standard\' "
                       "or \'reward low fn rate\' or \'reward low fp rate\'.")

    if self.rawData is None:
      self.rawData = getCSVData(self.dataPath)

    traces = []

    traces.append(self._addValues())

    # Anomaly detections traces:
    for i,d in enumerate(detectors):
      threshold = self.thresholds[d][scoreProfile]["threshold"]

      resultsData = getCSVData(os.path.join(self.resultsDir, resultsPaths[i]))

      FP, TP = self._parseDetections(resultsData, threshold)

      fpTrace, tpTrace = self._addDetections(
          "Detection by " + d, self.markers[i+1], FP, TP)

      traces.append(fpTrace)
      traces.append(tpTrace)

    if withLabels:
      traces.append(self._addLabels())

    if withWindows:
      traces.append(self._addWindows())

    if withProbation:
      traces.append(self._addProbation())

    # Create plotly Data and Layout objects:
    data = Data(traces)
    layout = self._createLayout("Anomaly Detections for " + self.dataName)

    # Query plotly
    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig)
    print "Detections plot URL: ", plot_url

    return plot_url


  def _parseDetections(self, resultsData, threshold):
    """Return false positives and true positives."""
    windows = getJSONData(
      os.path.join(self.labelsDir, "combined_windows.json"))[self.dataFile]

    detections = resultsData[resultsData["anomaly_score"] >= threshold]

    FP = detections[detections["label"] == 0]
    TP = []
    for window in windows:
      start = pd.to_datetime(window[0])
      end = pd.to_datetime(window[1])
      detection = self.getTPDetection(detections, (start, end))
      if detection:
        TP.append(detection)

    return FP, TP


  @staticmethod
  def getTPDetection(detections, windowTimes):
    """Returns the first occurence of a detection w/in the window times."""
    for detection in detections.iterrows():
      detectionTime = pd.to_datetime(detection[1]["timestamp"])
      if detectionTime > windowTimes[0] and detectionTime < windowTimes[1]:
          return detection
    return None


  def _addDetections(self, name, symbol, FP, TP):
    """Plot markers at anomaly detections; standard is for open shapes."""
    symbol = symbol + "-open"
    # FPs:
    fpTrace = Scatter(x=FP["timestamp"],
                      y=FP["value"],
                      mode="markers",
                      name=name,
                      text=["anomalous data"],
                      marker=Marker(
                        color="rgb(200, 20, 20)",
                        size=15.0,
                        symbol=symbol,
                        line=Line(
                          color="rgb(200, 20, 20)",
                          width=2
                        )
                      ))
    # TPs:
    tpTrace = Scatter(x=[tp[1]["timestamp"] for tp in TP],
                      y=[tp[1]["value"] for tp in TP],
                      mode="markers",
                      name=name,
                      text=["anomalous data"],
                      marker=Marker(
                        color="rgb(20, 200, 20)",
                        size=15.0,
                        symbol=symbol,
                        line=Line(
                          color="rgb(20, 200, 20)",
                          width=2
                        )
                      ))

    return fpTrace, tpTrace


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

  for i in xrange(len(dataFiles)):
    dataPlotter = PlotNAB(
        dataFile=dataFiles[i],
        dataName="Labels inspection for " + dataFiles[i])
    dataPlotter.plotRawData(
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
  #
  # assert len(dataFiles) == len(dataNames)
  #
  # # Create the list of result filenames for each detector
  # allResultsFiles = []
  # for f in dataFiles:
  #   resultFiles = []
  #   for d in detectors:
  #     filename = d + "/"+f.replace("/","/"+d+"_")
  #     resultFiles.append(filename)
  #   allResultsFiles.append(resultFiles)
  #
  # # Now plot everything
  # for i in range(len(dataFiles)):
  #   dataPlotter = PlotNAB(
  #       dataFile=dataFiles[i],
  #       dataName=dataNames[i])
  #   dataPlotter.plotMultipleDetectors(
  #       allResultsFiles[i],
  #       detectors=detectors,
  #       scoreProfile="standard",
  #       withLabels=False,
  #       withWindows=True,
  #       withProbation=True)
