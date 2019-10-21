# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2017, Numenta, Inc.  Unless you have an agreement
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

"""Plotting utility."""

import argparse
import itertools
import os
import sys
import tempfile

import pandas as pd

import plotly.offline
import plotly.plotly

from plotly.graph_objs import (
    Bar, Figure, Layout, Line, Margin, Marker, Scatter)

try:
  import simplejson as json
except ImportError:
  import json

MARKERS = ("circle", "diamond", "square", "cross", "triangle-up", "hexagon",
           "triangle-down")
WIDTH = 800
HEIGHT = 500
SCALE = 3.0



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
               dataName=None,
               offline=False):
    self.offline = offline
    if offline:
      self.py = plotly.offline
    else:
      self.py = plotly.plotly
      self._plotly_sign_in(self.py, username, apiKey)

    self._setupDirectories()
    self._getThresholds()

    # Setup data
    self.dataFile = dataFile
    self.dataName = dataName
    self.dataPath = os.path.join(self.dataDir, dataFile)
    self.rawData = getCSVData(self.dataPath) if self.dataPath else None


  @staticmethod
  def _plotly_sign_in(py, username=None, apiKey=None):
    try:
      apiKey = apiKey if apiKey else os.environ["PLOTLY_API_KEY"]
    except:
      print ("Missing PLOTLY_API_KEY environment variable. If you have a "
        "key, set it with $ export PLOTLY_API_KEY=api_key\n"
        "You can retrieve a key by registering for the Plotly API at "
        "http://www.plot.ly")
      raise OSError("Missing API key.")
    try:
      username = username if username else os.environ["PLOTLY_USERNAME"]
    except:
      print ("Missing PLOTLY_USERNAME environment variable. If you have a "
        "username, set it with $ export PLOTLY_USERNAME=username\n"
        "You can sign up for the Plotly API at http://www.plot.ly")
      raise OSError("Missing username.")

    py.sign_in(username, apiKey)


  def _setupDirectories(self):
    root = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    self.configDir = os.path.abspath(os.path.join(root, "config"))
    self.dataDir = os.path.abspath(os.path.join(root, "data"))
    self.labelsDir = os.path.abspath(os.path.join(root, "labels"))
    self.resultsDir = os.path.abspath(os.path.join(root, "results"))


  def _getThresholds(self):
    thresholdsPath = os.path.join(self.configDir, "thresholds.json")
    with open(thresholdsPath) as f:
      self.thresholds = json.load(f)


  @staticmethod
  def _addValues(data, start=None, end=None):
    """Return data values trace."""
    if start is None:
      start = data["timestamp"][0]
    if end is None:
      end = data["timestamp"].iloc[-1]
    mask = ((data["timestamp"] >= start) &
            (data["timestamp"] <= end))
    return Scatter(x=data["timestamp"][mask],
                   y=data["value"][mask],
                   name="value",
                   line=dict(
                     width=1.5
                   ),
                   showlegend=False)


  @staticmethod
  def _addScores(data, value, title, start=None, end=None):
    """return data values trace."""
    if start is None:
      start = data["timestamp"][0]
    if end is None:
      end = data["timestamp"].iloc[-1]
    mask = ((data["timestamp"] >= start) &
            (data["timestamp"] <= end))
    return Scatter(x=data["timestamp"][mask],
                   y=data[value][mask],
                   name=title,
                   showlegend=False)


  @staticmethod
  def _addLabels(data, labels, target="value", start=None, end=None):
    """return plotly trace for anomaly labels."""
    if start is None:
      start = data["timestamp"][0]
    if end is None:
      end = data["timestamp"].iloc[-1]

    x = []
    y = []
    for label in labels:
      row = data[data.timestamp == label]
      if ((row["timestamp"] >= start).values[0] and
          (row["timestamp"] <= end).values[0]):
        x.append(row["timestamp"])
        y.append(row[target])

    if x:
      x = pd.concat(x)
      y = pd.concat(y)

    return Scatter(x=x,
                   y=y,
                   mode="markers",
                   name="Ground Truth Anomaly",
                   text=["Anomalous Instance"],
                   marker=dict(
                     color="rgb(200, 20, 20)",
                     size=10,
                     symbol=MARKERS[0]
                   ))


  def _addWindows(self, start=None, end=None):
    """Return plotly trace for anomaly windows."""
    if start is None:
      start = self.rawData["timestamp"][0]
    if end is None:
      end = self.rawData["timestamp"].iloc[-1]
    mask = ((self.rawData["timestamp"] >= start) &
            (self.rawData["timestamp"] <= end))

    windows = getJSONData(
      os.path.join(self.labelsDir, "combined_windows.json"))[self.dataFile]

    x = []
    delta = (pd.to_datetime(self.rawData["timestamp"].iloc[1]) -
             pd.to_datetime(self.rawData["timestamp"].iloc[0]))
    minutes = int(delta.total_seconds() / 60)
    for window in windows:
      windowStart = max(pd.to_datetime(window[0]), pd.to_datetime(start))
      windowEnd = min(pd.to_datetime(window[1]), pd.to_datetime(end))
      x.extend(pd.date_range(windowStart, windowEnd, freq=str(minutes) + "Min").tolist())

    maxVal = self.rawData.value.max()
    y = [maxVal for _ in x]

    return Bar(x=x,
               y=y,
               name="Anomaly Window",
               marker=dict(
                 color="rgb(220, 100, 100)"
               ),
               opacity=0.3)


  def _addProbation(self, start=None, end=None):
    if start is None:
      start = self.rawData["timestamp"][0]
    if end is None:
      end = self.rawData["timestamp"].iloc[-1]
    mask = ((self.rawData["timestamp"] >= start) &
            (self.rawData["timestamp"] <= end))

    length = min(int(0.15 * len(self.rawData)), 750)
    x = self.rawData["timestamp"].iloc[:length][mask]
    y = [self.rawData.value.max() for _ in x]

    return Bar(x=x,
               y=y,
               name="Probationary Period",
               marker=dict(
                 color="rgb(0, 0, 200)"
               ),
               opacity=0.2)


  @staticmethod
  def _createLayout(title=None, xLabel="Date", yLabel="Metric", fontSize=12,
                    width=WIDTH, height=HEIGHT):
    """Return plotly Layout object."""
    layoutArgs = {
        "title": title,
        "font": {"size": fontSize},
        "showlegend": False,
        "width": width,
        "height": height,
        "xaxis": dict(
            title=xLabel,
        ),
        "yaxis": dict(
            title=yLabel,
            domain=[0, 1],
        ),
        "barmode": "stack",
        "bargap": 0}
    margins = {"l": 70, "r": 30, "b": 50, "t": 90, "pad": 4}
    if title is None:
      margins["t"] -= 70
    if fontSize > 12:
      margins["l"] += (fontSize - 12) * 3
      margins["b"] += (fontSize - 12) * 3
    layoutArgs["margin"] = margins
    return Layout(**layoutArgs)


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

    traces.append(self._addValues(self.rawData))

    # Anomaly detections traces:
    for i,d in enumerate(detectors):
      threshold = self.thresholds[d][scoreProfile]["threshold"]

      resultsData = getCSVData(os.path.join(self.resultsDir, resultsPaths[i]))

      FP, TP = self._parseDetections(resultsData, threshold)

      fpTrace, tpTrace = self._addDetections(
          "Detection by " + d, MARKERS[i+1], FP, TP)

      traces.append(fpTrace)
      traces.append(tpTrace)

    if withLabels:
      labels = getJSONData(os.path.join(
          self.labelsDir, "combined_labels.json"))[self.dataFile]
      traces.append(self._addLabels(self.rawData, labels, target="value"))

    if withWindows:
      traces.append(self._addWindows())

    if withProbation:
      traces.append(self._addProbation())

    # Create plotly Layout object:
    layout = self._createLayout("Anomaly Detections for " + self.dataName)

    # Query plotly
    fig = Figure(data=traces, layout=layout)
    plot_url = self.py.plot(fig)
    print("Detections plot URL: ", plot_url)

    return plot_url


  def plot(self,
           value="value",
           fontSize=12,
           start=None,
           end=None,
           xLabel=None,
           yLabel=None,
           width=WIDTH,
           height=HEIGHT,
           withLabels=False,
           withWindows=False,
           withProbation=False,
           plotPath=None):
    """Plot the data stream."""
    if value == "value":
      if yLabel is None:
        yLabel = "Metric"
    elif value == "raw":
      value = "raw_score"
      if yLabel is None:
        yLabel = "Prediction Error"
    elif value == "likelihood":
      value = "anomaly_score"
      if yLabel is None:
        yLabel = "Anomaly Likelihood"
    else:
      raise ValueError("Unknown value type '%s'".format(value))

    detector = "numenta"
    dataDir, dataFile = os.path.split(self.dataPath)
    dataDir = os.path.split(dataDir)[1]
    resultsFile = detector + "_" + dataFile
    resultsPath = os.path.join(os.path.dirname(__file__), os.path.pardir, "results", detector, dataDir, resultsFile)
    resultsData = getCSVData(resultsPath)

    traces = []

    traces.append(self._addScores(
        resultsData, value, yLabel, start, end))

    if withLabels:
      labels = getJSONData(os.path.join(
          self.labelsDir, "combined_labels.json"))[self.dataFile]
      traces.append(self._addLabels(resultsData, labels, target=value, start=start, end=end))

    if withWindows:
      traces.append(self._addWindows(start=start, end=end))

    if withProbation:
      traces.append(self._addProbation(start=start, end=end))

    # Create plotly Layout object:
    layout = self._createLayout(self.dataName, xLabel=xLabel, yLabel=yLabel, fontSize=fontSize, width=width, height=height)

    # Query plotly
    fig = Figure(data=traces, layout=layout)
    if plotPath is None:
      # We temporarily switch to a temp directory to avoid overwriting the
      # previous plot when in offline mode.
      cwd = os.getcwd()
      tempBase = os.path.join(cwd, "plot_")
      tempDir = tempfile.mkdtemp(prefix=tempBase)
      try:
        os.chdir(tempDir)
        plotPath = self.py.plot(fig)
        print("Data plot URL: ", plotPath)
      finally:
        os.chdir(cwd)
    else:
      self.py.image.save_as(fig, plotPath, width=width, height=height, scale=SCALE)

    return plotPath


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
                      marker=dict(
                        color="rgb(200, 20, 20)",
                        size=15.0,
                        symbol=symbol,
                        line=dict(
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
                      marker=dict(
                        color="rgb(20, 200, 20)",
                        size=15.0,
                        symbol=symbol,
                        line=dict(
                          color="rgb(20, 200, 20)",
                          width=2
                        )
                      ))

    return fpTrace, tpTrace



def main():
  """Command-line script entry point.

  Usage:
    nab-plot --title="Machine Temperature Sensor Data" realKnownCause/machine_temperature_system_failure.csv
  """
  parser = argparse.ArgumentParser()

  # Content
  parser.add_argument("--value", dest="value", default="value",
                      choices=("value", "raw", "likelihood"))
  parser.add_argument("--start", dest="start", default=None)
  parser.add_argument("--end", dest="end", default=None)
  parser.add_argument("--labels", dest="labels", action="store_true")
  parser.add_argument("--no-labels", dest="labels", action="store_false")
  parser.set_defaults(labels=True)
  parser.add_argument("--windows", dest="windows", action="store_true")
  parser.add_argument("--probation", dest="probation", action="store_true")

  # Layout
  parser.add_argument("--title", dest="title")
  parser.add_argument("--xLabel", default="Date")
  parser.add_argument("--no-xLabel", dest="xLabel", action="store_const",
                      const=None)
  parser.add_argument("--yLabel", dest="yLabel")
  parser.add_argument("--fontSize", dest="fontSize", default=12, type=int, required=False)
  parser.add_argument("--width", dest="width", default=WIDTH, type=int)
  parser.add_argument("--height", default=HEIGHT, type=int)

  # Misc.
  parser.add_argument("--offline", dest="offline", action="store_true")
  parser.add_argument("--output", dest="output", default=None)

  # Which data set to plot
  parser.add_argument("file")
  args = parser.parse_args()
  if args.offline and args.output is not None:
    print("Plots cannot be saved to file in offline mode.")
    sys.exit(-1)
  path = args.file
  title = args.title
  labels = args.labels
  windows = args.windows
  probation = args.probation
  offline = args.offline
  output = args.output

  dataPlotter = PlotNAB(dataFile=path, dataName=title, offline=offline)
  dataPlotter.plot(
      value=args.value,
      fontSize=args.fontSize,
      start=args.start,
      end=args.end,
      xLabel=args.xLabel,
      yLabel=args.yLabel,
      width=args.width,
      height=args.height,
      withLabels=labels,
      withWindows=windows,
      withProbation=probation,
      plotPath=output,
  )
