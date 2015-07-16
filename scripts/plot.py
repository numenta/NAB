# ----------------------------------------------------------------------
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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
This file contains plotting tools for NAB data and results. Run this script to
generate example plots.
"""

import itertools
import os
import pandas as pd
import plotly.plotly as py

from plotly.graph_objs import (Bar,
                               Layout,
                               Line,
                               Marker,
                               Scatter)

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
               username=None):  ## TODO: handle datafile stuff here (i.e. rawData) b/c all subclasses use it

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
    """Data values trace"""
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
    delta = pd.to_datetime(self.rawData["timestamp"][1]) -
            pd.to_datetime(self.rawData["timestamp"][0])
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
    length = int(0.15 * len(self.rawData))
    x = self.rawData["timestamp"].ix[:length]
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
    """Return plotly Layout object"""
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


  def plot():
    """Generate plot by buidling plotly objects and querying plotly API."""
    raise NotImplementedError()



class PlotRawData(PlotNAB):
  """Class to plot raw data values of time-series data files."""
  
  def __init__(self,
               dataFile,
               dataName=""):
    super(PlotRawData, self).__init__()
  
    self.dataFile = dataFile
    self.dataName = dataName if dataName else dataFile
    self.dataPath = os.path.join(self.dataDir, dataFile)
  
  
  
  def plot(self,
           withLabels=False,
           withWindows=False,
           withProbation=False):
  
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
    layout = self._createLayout("Raw Data for " + self.dataName)

    # Query plotly
    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig)
    print "Data plot URL: ", plot_url

    return plot_url



class PlotMultipleDetectors(PlotNAB):
  """Class to plot detector results on a data file."""
  def __init__(self,
               dataFile,
               dataName=""):
    super(PlotMultipleDetectors, self).__init__()
  
    self.dataFile = dataFile
    self.dataName = dataName if dataName else dataFile
    self.dataPath = os.path.join(self.dataDir, dataFile)
  
  
  def plot(self,
           resultsPaths,  ## TODO: auto-generate paths from dataFile and detectors
           detectors=["numenta"],
           scoreProfile="standard",
           withLabels=True,
           withWindows=True,
           withProbation=True):

    if scoreProfile is not "standard" or not "reward_low_fn_rate" or not "reward_low_fp_rate":
      raise ValueError("Invalid scoring profile. Must be one of \'standard\' or \'reward low fn rate\' or \'reward low fp rate\'.")

    
    self.rawData = getCSVData(os.path.join(self.dataPath))
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
  def getTPDetection(detections, windowTimes):  ## TODO: use generator to yield each time, rather than looping through all detections
    """Returns the first occurence of a detection w/in the window times."""
    for detection in detections.iterrows():
      detectionTime = pd.to_datetime(detection[1]["timestamp"])
      if detectionTime > windowTimes[0] and detectionTime < windowTimes[1]:
          return detection
    return None


  def _addDetections(self, name, symbol, FP, TP):
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

  # Examples:
  
  dataFiles = [
    "realKnownCause/machine_temperature_system_failure.csv",
    "realAWSCloudwatch/ec2_cpu_utilization_fe7f93.csv"]
  dataNames = [
    "Machine Temperature Sensor Data",
    "AWS Cloudwatch CPU Utilization Data"]
  resultsFiles = [
    "numenta/realKnownCause/numenta_machine_temperature_system_failure.csv",
    "skyline/realKnownCause/skyline_machine_temperature_system_failure.csv",
    "twitterADVec/realKnownCause/twitter_machine_temperature_system_failure.csv",
    "twitterADTs/realKnownCause/twitter_machine_temperature_system_failure.csv"]

  for i in xrange(len(dataFiles)):
    dataPlotter = PlotRawData(
      dataFiles[i],
      dataNames[i])
    dataPlotter.plot(
      withLabels=True,
      withWindows=False,
      withProbation=False)

  resultsPlotter = PlotMultipleDetectors(
    dataFiles[0],
    dataNames[0])
  resultsPlotter.plot(
    resultsFiles,
    detectors=["numenta", "skyline", "twitterADVec", "twitterADTs"],
    scoreProfile="standard",
    withLabels=False,
    withWindows=True,
    withProbation=True)
