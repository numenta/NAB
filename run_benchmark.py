#!/usr/bin/env python
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
import yaml

from optparse import OptionParser
from multiprocessing import Pool, cpu_count
from subprocess import call
from copy import deepcopy

from run_anomaly import runAnomaly
from analyze_results import analyzeResults

gPlotsAvailable = False
try:
  from plotly import plotly
  gPlotsAvailable = True
except ImportError:
  print "Plotly not installed. Plots will not be available."
  pass

def main(options):
  """
  Run the NAB corpus according to user options selected
  """

  # Load the config file
  with open(options.config) as configHandle:
    config = yaml.load(configHandle)

  # Use as many CPUs as are available
  numCPUs = cpu_count()

  # Decide if plots are an option
  plot = False
  if gPlotsAvailable and options.plotResults:
    plot = True

  # Run the data analysis portion unless asked not to
  if not options.analyzeOnly:

    pool = Pool(processes=numCPUs)

    # Collect a list of tasks to parralelize
    tasks = []

    # Loop over each desired anomaly detector
    for detector in config["AnomalyDetectors"]:

      # Loop over each desired data group
      for dataGroup in config["DataGroups"]:

        # Get list of files to process
        dataPath = os.path.join("data", dataGroup)
        dirContents = os.listdir(dataPath)
        csvNames = [name for name in dirContents if ".csv" in name]

        # Loop over csvs in that directory
        for fileName in csvNames:
          subOpt = deepcopy(options)
          subOpt.inputFile = os.path.join(dataPath, fileName)
          subOpt.detector = detector
          subOpt.dataGroup = dataGroup
          # Add in options used when running run_anomaly.py stand-alone
          subOpt.min = None
          subOpt.max = None
          subOpt.outputFile = None
          subOpt.outputDir = config['ResultsDirectory']
          tasks.append(subOpt)

    print "Running %d tasks using %d cores ..." % (len(tasks), numCPUs)

    # Process those files in parallel
    pool.map(runAnomaly, tasks)

  # Results have been generated. Analyze them unless asked not to.
  if not options.resultsOnly:

    tasks = []
    for detector in config["AnomalyDetectors"]:
      subOpt = deepcopy(options)
      subOpt.plot = plot
      resultsDir = os.path.join(config['ResultsDirectory'], detector)
      subOpt.resultsDir = resultsDir
      # Plotting in parallel fails, so don't use pool
      if plot:
        analyzeResults(subOpt)
      else:
        tasks.append(subOpt)

    if tasks:
      pool = Pool(processes=numCPUs)
      pool.map(analyzeResults, tasks)


if __name__ == "__main__":

  parser = OptionParser()
  parser.add_option("-a", "--analyzeOnly", help="Analyze results in the "
                    "results directory only.", dest="analyzeOnly",
                    default=False,
                    action="store_true")
  parser.add_option("-r", "--resultsOnly", help="Generate detector results but "
                    "do not analyze results files.",
                    dest="resultsOnly", default=False, action="store_true")
  parser.add_option("-p", "--plot", help="If you have Plotly installed "
                    "this option will plot results and ROC curves for each "
                    "dataset.",
                    dest="plotResults", default=False, action="store_true")
  parser.add_option("--verbosity", default=0, help="Increase the amount and "
                    "detail of output by setting this greater than 0.")
  parser.add_option("--config", default="benchmark_config.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  options, args = parser.parse_args()

  main(options)


