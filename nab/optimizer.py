# ----------------------------------------------------------------------
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
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
import os

from nab.sweeper import Sweeper
from nab.util import convertResultsPathToDataPath



def optimizeThreshold(args):
  """Optimize the threshold for a given combination of detector and profile.

  @param args       (tuple)   Arguments necessary for the objective function.

  @param tolerance  (float)   Number used to determine when optimization has
                              converged to a sufficiently good score.

  @return (dict) Contains:
        "threshold" (float)   Threshold that returns the largest score from the
                              Objective function.

        "score"     (float)   The score from the objective function given the
                              threshold.
  """
  (pool,
   detectorName,
   profileName,
   costMatrix,
   resultsDetectorDir,
   resultsCorpus,
   corpusLabel,
   probationaryPercent,
   scoreFlag) = args

  sweeper = Sweeper(
    probationPercent=probationaryPercent,
    costMatrix=costMatrix
  )

  # First, get the sweep-scores for each row in each data set
  allAnomalyRows = []
  for relativePath, dataSet in resultsCorpus.dataFiles.iteritems():
    if "_scores.csv" in relativePath:
      continue

    # relativePath: raw dataset file,
    # e.g. 'artificialNoAnomaly/art_noisy.csv'
    relativePath = convertResultsPathToDataPath( \
      os.path.join(detectorName, relativePath))

    windows = corpusLabel.windows[relativePath]
    labels = corpusLabel.labels[relativePath]
    timestamps = labels['timestamp']
    anomalyScores = dataSet.data["anomaly_score"]

    curAnomalyRows = sweeper.calcSweepScore(
      timestamps,
      anomalyScores,
      windows,
      relativePath
    )
    allAnomalyRows.extend(curAnomalyRows)

  # Get scores by threshold for the entire corpus
  scoresByThreshold = sweeper.calcScoreByThreshold(allAnomalyRows)
  scoresByThreshold = sorted(scoresByThreshold, key=lambda x: x.score, reverse=True)
  bestParams = scoresByThreshold[0]

  print("Optimizer found a max score of {} with anomaly threshold {}.".format(
    bestParams.score, bestParams.threshold
  ))

  return {
    "threshold": bestParams.threshold,
    "score": bestParams.score
  }
