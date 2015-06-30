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

from plotly.graph_objs import *

try:
  import simplejson as json
except ImportError:
  import json



class PlotNAB():
  """Plot NAB data and results files with the plotly API."""

  def __init__(self,
               apiKey=None,
               username=None):
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


  def _setupDirectories(self):
    root = os.path.dirname(os.path.realpath(__file__))
    self.configDir = os.path.abspath(os.path.join(root, "..", "config"))
    self.dataDir = os.path.abspath(os.path.join(root, "..", "data"))
    self.labelsDir = os.path.abspath(os.path.join(root, "..", "labels"))
    self.resultsDir = os.path.abspath(os.path.join(root, "..", "results"))


  def plotRawData(self,
                  dataPath,
                  dataName,
                  withLabels=False,
                  withWindows=False,
                  withProbation=False):
  
    rawData = self.getRawData(os.path.join(self.dataDir, dataPath))

    traces = []

    # Value trace:
    traces.append(Scatter(
                          x=rawData['timestamp'],
                          y=rawData['value'],
                          name='Value',
                          line=Line(
                            width=0.7
                          ),
                          showlegend=False
                        ))
    
    if withLabels:
      traces.append(self._addLabels(rawData, dataPath))
    
    if withWindows:
      traces.append(self._addWindows(rawData, dataPath))
    
    if withProbation:
      traces.append(self._addProbation(rawData))

    # Create plotly Data object with the traces.
    data = Data(traces)
  
    # Create plotly Layout object.
    layout = Layout(
                    title='Raw Data for ' + dataName,
                    showlegend=False,
                    width=1000,
                    height=600,
                    xaxis=XAxis(
                      title='Date'
                    ),
                    yaxis=YAxis(
                      title='Metric',
                      domain=[0, 1],
                      autorange=True,
                      autotick=True
                    ),
                    barmode='stack',
                    bargap=0
             )

    # Query plotly
    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig)
    print "Data plot URL: ", plot_url


  def plotResults(self,
                  resultsPath,
                  resultsName,
                  scoreProfile='standard',
                  withWindows=None,
                  withProbation=True):
    """
    To plot anomaly windows, set withWindows = data file name.
    """

    if scoreProfile is not 'standard' or not 'reward_low_fn_rate' or not 'reward_low_fp_rate':
      raise ValueError("Invalid scoring profile. Must be one of \'standard\' or \'reward low fn rate\' or \'reward low fp rate\'.")

    resultsData = self.getResultsData(os.path.join(self.resultsDir, resultsPath))

    traces = []

    # Anomaly scores trace:
    traces.append(Scatter(
                          x=resultsData['timestamp'],
                          y=resultsData['anomaly_score'],
                          name='Anomaly Score',
                          line=Line(
                            width=0.7,
                            color='rgb(80, 200, 80)'
                          ),
                          showlegend=False
                  ))

    # Anomaly detections trace:
    threshold = self._getThreshold(resultsPath.split('/')[0], scoreProfile)
    detections = resultsData[resultsData['anomaly_score'] >= threshold]
    traces.append(Scatter(
                          x=detections['timestamp'],
                          y=detections['anomaly_score'],
                          mode='markers',
                          name='Detected anomaly',
                          text=['anomalous data'],
                          marker=Marker(
                            color='rgb(200, 20, 20)',
                            size=5.0,
                            symbol='triangle-open'
                          )
                  ))
    
    if withWindows:
      traces.append(self._addWindows(resultsData, withWindows))
    
    if withProbation:
      traces.append(self._addProbation(resultsData))
    
    # Create plotly Data object with the traces.
    data = Data(traces)

    # Create plotly Layout object.
    layout = Layout(
                    title='Results for ' + resultsName,
                    showlegend=True,
                    width=1000,
                    height=600,
                    xaxis=XAxis(
                      title='Date'
                    ),
                    yaxis=YAxis(
                      title='Anomaly Score',
                      domain=[0, 1],
                      range=[0, 1.05],
                      autotick=True
                    ),
                    barmode='stack',
                    bargap=0,
             )

    # Query plotly
    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig)
    print "Results plot URL: ", plot_url


  def _addLabels(self, df, dataPath):
    # Anomaly labels trace.
    labels = self.getData(
      os.path.join(self.labelsDir, "combined_labels.json"), dataPath)
    
    x = []
    y = []
    for label in labels:
      row = df[df.timestamp == label]
      x.append(row['timestamp'])
      y.append(row['value'])
    
    return Scatter(
                   x=x,
                   y=y,
                   mode='markers',
                   name='Ground Truth Anomaly',
                   text=['anomalous instance'],
                   marker=Marker(
                     color='rgb(200, 20, 20)',
                     size=7.0,
                     symbol='circle-open'
                   )
           )


  def _addWindows(self, df, dataPath):
    # Anomaly windows trace.
    windows = self.getData(
      os.path.join(self.labelsDir, "combined_windows.json"), dataPath)
    
    x = []
    delta = pd.to_datetime(df['timestamp'][1]) - pd.to_datetime(df['timestamp'][0])
    minutes = int(delta.total_seconds() / 60)
    for window in windows:
      start = pd.to_datetime(window[0])
      end = pd.to_datetime(window[1])
      x.append(pd.date_range(start, end, freq=str(minutes) + 'Min').tolist())

    x = list(itertools.chain.from_iterable(x))
    y = [df.value.max() for _ in x]

    return Bar(
               x=x,
               y=y,
               name='Anomaly Window',
               marker=Marker(
                 color='rgb(220, 100, 100)'
               ),
               opacity=0.3
           )


  @staticmethod
  def _addProbation(df):
    # Probationary period trace.
    length = int(0.15 * len(df))
    x = df['timestamp'].ix[:length]
    y = [df.value.max() for _ in x]

    return Bar(
               x=x,
               y=y,
               name='Probationary Period',
               marker=Marker(
                 color='rgb(0, 0, 200)'
               ),
               opacity=0.3
           )


  @staticmethod
  def getResultsData(dataPath):
    """Get data from results CSV."""
    try:
      data = pd.read_csv(dataPath)
    except IOError("Invalid path to data file."):
      return

    return data


  @staticmethod
  def getRawData(dataPath):
    """Get data from raw data file."""
    try:
      data = pd.read_csv(dataPath)
    except IOError("Invalid path to data file."):
      return

    return data


  @staticmethod
  def getData(jsonPath, key):
    with open(jsonPath) as f:
      dataDict = json.load(f)
    return dataDict[key]


  def _getThreshold(self, detector, profile):
    thresholdsPath = os.path.join(self.configDir, "thresholds.json")
    with open(thresholdsPath) as f:
      thresholds = json.load(f)
    return thresholds[detector][profile]["threshold"]


if __name__ == "__main__":

  # Example:
  
  plotter = PlotNAB()
  
#  dataFiles = [
#    'realKnownCause/machine_temperature_system_failure.csv',
#    'realAWSCloudwatch/ec2_cpu_utilization_fe7f93.csv']
#  dataNames = [
#    'Machine Temp System Failure',
#    'AWS Cloudwatch CPU Utilization']
#  resultsFiles = [
#    'numenta/realKnownCause/numenta_machine_temperature_system_failure.csv',
#    'numenta/realAWSCloudwatch/numenta_ec2_cpu_utilization_fe7f93.csv']
#  resultsNames = [
#    'Numenta HTM Detections - Machine Temp System Failure',
#    'Numenta HTM Detections - AWS CLoudwatch CPU Utilization']

  dataFiles = [
    'realAWSCloudwatch/rds_cpu_utilization_cc0c53.csv',
    'realAWSCloudwatch/rds_cpu_utilization_cc0c53.csv']
  dataNames = [
    '',
    '']
  resultsFiles = [
    'numenta/realAWSCloudwatch/numenta_rds_cpu_utilization_cc0c53.csv',
    'skyline/realAWSCloudwatch/skyline_rds_cpu_utilization_cc0c53.csv']
  resultsNames = [
    'Numenta HTM Detections - ',
    'Skyline Detections - ']

  for i in xrange(len(dataFiles)):
    plotter.plotRawData(
      dataFiles[i],
      dataNames[i],
      withLabels=True,
      withWindows=True,
      withProbation=False
    )
    plotter.plotResults(
      resultsFiles[i],
      resultsNames[i],
      scoreProfile='standard',
      withWindows=dataFiles[i],
      withProbation=True
    )

