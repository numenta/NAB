#! /usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
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
Scatter plots to analyze anomaly detections for the NAB benchmark dataset.
"""

import argparse
import matplotlib.pyplot as plt
import os
try:
  import simplejson as json
except ImportError:
  import json

from nab.corpus import Corpus
from nab.util import checkInputs



def plotAnomaliesAndWindows(anomalyScores, labels, values, threshold,
                            relativePath, filePath):
  """
  Ground truth anomaly windows are plotted with black '+'.
  Anomaly likelihoods are plotted with 'o', red if above the threshold, green
  otherwise.
  Line plot is the raw data.
  """
  # TODO: add key
  ii = range(len(labels))
  jj = [i for i in ii if anomalyScores[i] >= threshold]
  kk = [i for i in ii if labels[i] == 1]
  norm_values = [float(v)/max(values) for v in values]

  plt.figure()
  plt.plot(ii, norm_values,
    color='k', alpha=0.2)
  plt.scatter(ii, anomalyScores,
    color='g', s=20, alpha=0.3, marker="o")
  plt.scatter(jj, anomalyScores[anomalyScores >= threshold],
    color='r', s=20, alpha=0.7, marker="o")
  plt.scatter(kk, labels[labels==1],
    color='k', s=20, alpha=1.0, marker="+")
  plt.axis([0, len(labels), 0, 1.1])
  plt.title(relativePath)
  plt.show()
  
  if filePath:
    pylab.savefig(filePath, bbox_inches="tight")


def main(args):
  with open(args.thresholdsFile) as t:
    thresholds = json.load(t)

  for detectorName in args.detectors:
    print "Getting results files for %s detector..." % detectorName
    
    resultsDetectorDir = os.path.join(args.resultsDir, detectorName)
    resultsCorpus = Corpus(resultsDetectorDir).dataFiles
    if args.specificFiles:
      resultsCorpus = dict([(i, resultsCorpus[i])
                            for i in args.specificFiles if i in resultsCorpus])

    print "Now plotting..."
    
    for relativePath, dataSet in resultsCorpus.iteritems():
      if "_scores.csv" in relativePath:
        continue
      
      if args.savePlots:
        filePath = args.destPath + "/" + relativePath[:-4] + ".png"
        print "Scatterplots to be written to", filePath
      else:
        filePath = None

      plotAnomaliesAndWindows(dataSet.data["anomaly_score"],
                              dataSet.data["label"],
                              dataSet.data["value"],
                              thresholds[detectorName]["standard"]["threshold"],
                              relativePath,
                              filePath)

  print "Done with plotting all results files"


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("--resultsDir",
                      default="results",
                      help="This holds all the data files for the corpus.")

  parser.add_argument("--destPath",
                      default="results/scatterplots",
                      help="Where the scatterplot files will be stored.")

  parser.add_argument("--thresholdsFile",
                      default="config/thresholds.json",
                      help="Where the detectors' anomaly threshold values are \
                      stored.")

  parser.add_argument("-f", "--specificFiles",
                    nargs="*",
                    type=str,
                    default=[],
                    help="Space separated list of datafile(s) to use.")

  parser.add_argument("-d", "--detectors",
                    nargs="*",
                    type=str,
                    default=["numenta", "skyline"],
                    help="Space separated list of detector(s) to use.")
                    
  parser.add_argument("--skipConfirmation",
                    default=False,
                    action="store_true",
                    help="If specified will skip the user confirmation step.")
                    
  parser.add_argument("--savePlots",
                    default=False,
                    action="store_false",
                    help="If specified will save plots to the destPath.")

  args = parser.parse_args()

  if args.skipConfirmation or checkInputs(args):
    main(args)
