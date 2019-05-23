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
import pandas

from nab.sweeper import Sweeper
from nab.util import convertResultsPathToDataPath


def scoreCorpus(threshold, args):
  """Scores the corpus given a detector's results and a user profile.

  Scores the corpus in parallel.

  @param threshold  (float)   Threshold value to convert an anomaly score value
                              to a detection.

  @param args       (tuple)   Contains:

    pool                (multiprocessing.Pool)  Pool of processes to perform
                                                tasks in parallel.
    detectorName        (string)                Name of detector.

    profileName         (string)                Name of scoring profile.

    costMatrix          (dict)                  Cost matrix to weight the
                                                true positives, false negatives,
                                                and false positives during
                                                scoring.
    resultsDetectorDir  (string)                Directory for the results CSVs.

    resultsCorpus       (nab.Corpus)            Corpus object that holds the per
                                                record anomaly scores for a
                                                given detector.
    corpusLabel         (nab.CorpusLabel)       Ground truth anomaly labels for
                                                the NAB corpus.
    probationaryPercent (float)                 Percent of each data file not
                                                to be considered during scoring.
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

  args = []
  for relativePath, dataSet in resultsCorpus.dataFiles.items():
    if "_scores.csv" in relativePath:
      continue

    # relativePath: raw dataset file,
    # e.g. 'artificialNoAnomaly/art_noisy.csv'
    relativePath = convertResultsPathToDataPath(
      os.path.join(detectorName, relativePath))

    # outputPath: dataset results file,
    # e.g. 'results/detector/artificialNoAnomaly/detector_art_noisy.csv'
    relativeDir, fileName = os.path.split(relativePath)
    fileName =  detectorName + "_" + fileName
    outputPath = os.path.join(resultsDetectorDir, relativeDir, fileName)

    windows = corpusLabel.windows[relativePath]
    labels = corpusLabel.labels[relativePath]
    timestamps = labels['timestamp']

    anomalyScores = dataSet.data["anomaly_score"]

    args.append((
      detectorName,
      profileName,
      relativePath,
      outputPath,
      threshold,
      timestamps,
      anomalyScores,
      windows,
      costMatrix,
      probationaryPercent,
      scoreFlag))

  # Using `map_async` instead of `map` so interrupts are properly handled.
  # See: http://stackoverflow.com/a/1408476
  # Magic number is a timeout in seconds.
  results = pool.map_async(scoreDataSet, args).get(999999)

  # Total the 6 scoring metrics for all data files
  totals = [None]*3 + [0]*6
  for row in results:
    for i in range(6):
      totals[i+3] += row[i+4]

  results.append(["Totals"] + totals)

  resultsDF = pandas.DataFrame(data=results,
                               columns=("Detector", "Profile", "File",
                                        "Threshold", "Score", "TP", "TN",
                                        "FP", "FN", "Total_Count"))

  return resultsDF


def scoreDataSet(args):
  """Function called to score each dataset in the corpus.

  @param args   (tuple)  Arguments to get the detection score for a dataset.

  @return       (tuple)  Contains:
    detectorName  (string)  Name of detector used to get anomaly scores.

    profileName   (string)  Name of profile used to weight each detection type.
                            (tp, tn, fp, fn)

    relativePath  (string)  Path of dataset scored.

    threshold     (float)   Threshold used to convert anomaly scores to
                            detections.

    score         (float)   The score of the dataset.

    counts, tp    (int)     The number of true positive records.

    counts, tn    (int)     The number of true negative records.

    counts, fp    (int)     The number of false positive records.

    counts, fn    (int)     The number of false negative records.

    total count   (int)     The total number of records.
  """
  (detectorName,
   profileName,
   relativePath,
   outputPath,
   threshold,
   timestamps,
   anomalyScores,
   windows,
   costMatrix,
   probationaryPercent,
   scoreFlag) = args

  scorer = Sweeper(
    probationPercent=probationaryPercent,
    costMatrix=costMatrix
  )

  (scores, bestRow) = scorer.scoreDataSet(
    timestamps,
    anomalyScores,
    windows,
    relativePath,
    threshold,
  )

  if scoreFlag:
    # Append scoring function values to the respective results file
    dfCSV = pandas.read_csv(outputPath, header=0, parse_dates=[0])
    dfCSV["S(t)_%s" % profileName] = scores
    dfCSV.to_csv(outputPath, index=False)

  return (detectorName, profileName, relativePath, threshold, bestRow.score,
          bestRow.tp, bestRow.tn, bestRow.fp, bestRow.fn, bestRow.total)
