# Copyright 2014-2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import os

from nab.sweeper import Sweeper
from nab.util import convertResultsPathToDataPath



def optimizeThreshold(args):
  """Optimize the threshold for a given combination of detector and profile.

  @param args       (tuple)   Contains:

    detectorName        (string)                Name of detector.

    costMatrix          (dict)                  Cost matrix to weight the
                                                true positives, false negatives,
                                                and false positives during
                                                scoring.
    resultsCorpus       (nab.Corpus)            Corpus object that holds the per
                                                record anomaly scores for a
                                                given detector.
    corpusLabel         (nab.CorpusLabel)       Ground truth anomaly labels for
                                                the NAB corpus.
    probationaryPercent (float)                 Percent of each data file not
                                                to be considered during scoring.

  @return (dict) Contains:
        "threshold" (float)   Threshold that returns the largest score from the
                              Objective function.

        "score"     (float)   The score from the objective function given the
                              threshold.
  """
  (detectorName,
   costMatrix,
   resultsCorpus,
   corpusLabel,
   probationaryPercent) = args

  sweeper = Sweeper(
    probationPercent=probationaryPercent,
    costMatrix=costMatrix
  )

  # First, get the sweep-scores for each row in each data set
  allAnomalyRows = []
  for relativePath, dataSet in resultsCorpus.dataFiles.items():
    if "_scores.csv" in relativePath:
      continue

    # relativePath: raw dataset file,
    # e.g. 'artificialNoAnomaly/art_noisy.csv'
    relativePath = convertResultsPathToDataPath(
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
  scoresByThreshold = sorted(
    scoresByThreshold,key=lambda x: x.score, reverse=True)
  bestParams = scoresByThreshold[0]

  print(("Optimizer found a max score of {} with anomaly threshold {}.".format(
    bestParams.score, bestParams.threshold
  )))

  return {
    "threshold": bestParams.threshold,
    "score": bestParams.score
  }
