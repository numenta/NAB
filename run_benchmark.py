#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

from multiprocessing import Pool, cpu_count
from subprocess import call

def runAnomaly(inputFile):

	cmd = "python run_anomaly.py --inputFile %s" % inputFile
	call(cmd, shell=True)

def analyzeResults(inputFile, plot = False):

	cmd = "python analyze_results.py --inputFile %s " % inputFile
	if plot:
		cmd += "--plot"
	call(cmd, shell=True)

if __name__ == "__main__":

	# Use as many CPUs as are available
	numCPUs = cpu_count()
	pool = Pool(processes=numCPUs)

	# Get list of files to process
	dataPath = os.path.join("data", "artificialWithAnomaly")
	dirContents = os.listdir(dataPath)
	csvNames = [name for name in dirContents if ".csv" in name]
	filePaths = [os.path.join(dataPath, fileName) for 
				 fileName in csvNames]

	# Process those files in parallel
	#pool.map(runAnomaly, filePaths)

	# Results have been generated. Analyze them.
	resultsDir = "results"
	resultsFilenames = ["anomaly_scores_" + fileName for fileName
						in csvNames]
	resultsPaths = [os.path.join(resultsDir, fileName) for 
				 	fileName in resultsFilenames]

	plot = True
	# Plotly doesn't work well in parrallel so do analysis in sequence
	for resultPath in resultsPaths:
		analyzeResults(resultPath, plot)
