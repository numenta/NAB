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

import collections
import copy
import os

from nab.scorer import scaledSigmoid
from nab import util

DataRow = collections.namedtuple("DataRow", ("anomalyScore", "label"))
"""Input format for optimizer.

:param anomalyScore: the score returned by the detetor
:param label: the ground truth - True if the point is inside a window,
    False otherwise
"""

ThresholdResult = collections.namedtuple("ThresholdResult",
                                         ("score", "threshold", "counts"))
"""The return format from the optimizer.

:param score: the score computed for this detector with the corresponding
    threshold
:param threshold: the threshold used to compute the corresponding score
:param counts: a dict containing the number of points for:
    "tp" - true positives
    "tn" - true negatives
    "fp" - false positives
    "fn" - false negatives
"""

_WindowInfo = collections.namedtuple("_WindowInfo",
                                     ("start", "end", "detectedAnomalies"))
"""Private class with preprocessed window info.

:param start: the file-specific index of the first point in the window
:param end: the file-specific index of the last point in the window
:detectedAnomalies: a list of indices of points where the detector's
    anomaly score is higher than the current threshold. This is updated
    each time the threshold is lowered.
"""

_DataInfo = collections.namedtuple("_DataInfo",
                                   ("anomalyScore", "idx", "lastWindow"))
"""Private class with preprocessed info about a data row.

:param anomalyScore: the score returned by the detector
:param idx: the file-specific index of this row
:param lastWindow: The _WindowInfo instance that this row is in, or the
    last window precedign this row if this row is outside any window. None
    if no window has been seen yet in this file.
"""



def _processWindows(data):
  """Process the windows into a format for easy processing.

  :param data: a dict mapping each data file path to a list of DataRow
      instances for that file
  :returns: dict mapping data file path to list of _WindowInfo instances
  """
  anomalyWindows = collections.defaultdict(list)
  for path, rows in data.iteritems():
    start = None
    for i, row in enumerate(rows):
      if start is None and row.label:
        # Keep track of the start of the window
        start = i
      elif ((start is not None and not row.label) or
            (start is not None and i == len(rows) - 1)):
        # Store the window
        windowInfo = _WindowInfo(start=start, end=i-1,
                                 detectedAnomalies=[])
        anomalyWindows[path].append(windowInfo)
        start = None
    assert start is None

  return anomalyWindows



def _processData(data, anomalyWindows, probationaryFraction):
  """Process the data rows into a format for easy processing.

  The resulting _DataInfo instances that fall into the same window will
  have references to the same _WindowInfo instance and thus can see which
  other data rows have been detected so far in the
  _WindowInfo.detectedAnomalies list.

  :param data: a dict mapping each data file path to a list of ordered
      _DataRow instances for that file
  :param anomalyWindows: a dict mapping each data file path to a list of
      ordered _WindowInfo instances
  :param probationaryFraction: a float corresponding to the fraction of
      rows in each file that belong to the probationary period

  :returns: a list of _DataInfo instances for each row in all files
  """
  # All data points sorted by anomaly score. Each element is a tuple of
  # (anomalyScore, timestamp, mostRecentWindow, indexInFile)
  output = []
  for path, rows in data.iteritems():
    numRecords = len(rows)
    probationaryPeriod = util.getProbationPeriod(probationaryFraction,
                                                 numRecords)
    if len(os.path.split(path)[0]) == 0:
      print "Skipping summary file: ", path
      continue
    lastWindow = None
    nextWindowIdx = 0
    for i, row in enumerate(rows):
      if (len(anomalyWindows[path]) > nextWindowIdx and
          i >= anomalyWindows[path][nextWindowIdx].start):
        lastWindow = anomalyWindows[path][nextWindowIdx]
        nextWindowIdx += 1

      if i < probationaryPeriod:
        dataIdx = None
      else:
        dataIdx = i
      output.append(_DataInfo(anomalyScore=row.anomalyScore,
                            idx=dataIdx,
                            lastWindow=lastWindow))
      if output[-1].idx is None:
        assert output[-1].lastWindow is None, (output[-1], probationaryPeriod, path, len(rows))

  return output



def _windowRange(window):
  return window.end - window.start + 1



def computeScaledScoreInsideWindow(dataInfo):
  relativePosition = (float(dataInfo.idx - dataInfo.lastWindow.end - 1) /
                      _windowRange(dataInfo.lastWindow))
  return scaledSigmoid(relativePosition) / scaledSigmoid(-1.0)



def computeScaledScoreOutsideWindow(dataInfo):
  relativePosition = (float(dataInfo.idx - dataInfo.lastWindow.end) /
                      (_windowRange(dataInfo.lastWindow) - 1))
  return scaledSigmoid(relativePosition)



def _computeScoreChange(dataInfo, costMatrix):
  scoreChange = 0.0
  countsChange = collections.defaultdict(int)
  if dataInfo.lastWindow is None:
    # False positive before any windows
    if dataInfo.idx is not None:
      # Probationary period has passed
      scoreChange -= costMatrix["fpWeight"]

      # Update countsChange
      countsChange["tn"] -= 1
      countsChange["fp"] += 1
    else:
      # Do nothing, don't count the FP
      pass
  elif dataInfo.idx > dataInfo.lastWindow.end:
    # Outside window, contribute false positive
    scoreChange += (computeScaledScoreOutsideWindow(dataInfo) *
                    costMatrix["fpWeight"])

    # Update countsChange
    countsChange["tn"] -= 1
    countsChange["fp"] += 1
  elif len(dataInfo.lastWindow.detectedAnomalies) == 0:
    # First anomaly detected inside the window
    scoreChange += costMatrix["fnWeight"]
    scoreChange += (computeScaledScoreInsideWindow(dataInfo) *
                    costMatrix["tpWeight"])
    # Update the last windows list of detected anomalies
    dataInfo.lastWindow.detectedAnomalies.append(dataInfo)
    dataInfo.lastWindow.detectedAnomalies.sort(key=lambda di: di.idx)

    # Update countsChange
    countsChange["fn"] -= 1
    countsChange["tp"] += 1
  elif dataInfo.idx < dataInfo.lastWindow.detectedAnomalies[0]:
    # Not first instance of a detected anomaly but earliest in window
    windowRange = _windowRange(dataInfo.lastWindow)

    prevDataInfo = dataInfo.lastWindow.detectedAnomalies[0]
    scoreChange -= (computeScaledScoreInsideWindow(prevDataInfo) *
                    costMatrix["tpWeight"])

    scoreChange += (computeScaledScoreInsideWindow(dataInfo) *
                    costMatrix["tpWeight"])

    dataInfo.lastWindow.detectedAnomalies.append(dataInfo)
    dataInfo.lastWindow.detectedAnomalies.sort(key=lambda di: di.idx)

    # Update countsChange
    countsChange["fn"] -= 1
    countsChange["tp"] += 1
  else:
    # Not first or earliest anomaly in window
    dataInfo.lastWindow.detectedAnomalies.append(dataInfo)
    dataInfo.lastWindow.detectedAnomalies.sort(key=lambda di: di.idx)

    # Update countsChange
    countsChange["fn"] -= 1
    countsChange["tp"] += 1

  return scoreChange, countsChange



def _computeThresholdScores(data, numWindows, costMatrix):
  # Set up stats
  counts = {
    "tn": len(data),
    "tp": 0,
    "fp": 0,
    "fn": 0,
  }
  for dataInfo in data:
    if (dataInfo.lastWindow is not None and
        dataInfo.idx <= dataInfo.lastWindow.end):
      counts["tn"] -= 1
      counts["fn"] += 1

  # Now we iteratively compute the score for every possible threshold
  data = sorted(data, key=lambda di: di.anomalyScore, reverse=True)
  score = -(numWindows * costMatrix["fnWeight"])
  threshold = 2.0
  resultMap = {threshold: ThresholdResult(
      score=score, threshold=threshold, counts=copy.deepcopy(counts))}
  for dataInfo in data:
    threshold = dataInfo.anomalyScore
    scoreChange, countsChange = _computeScoreChange(dataInfo, costMatrix)
    score += scoreChange
    for k, v in countsChange.iteritems():
      counts[k] += v

    # Make sure that you replace any previous, intermediate score with the
    # same threshold since that would be an erroneous score.
    resultMap[threshold] = ThresholdResult(
      score=score, threshold=threshold, counts=copy.deepcopy(counts))

  return sorted(resultMap.values(), reverse=True, key=lambda v: v.score)



def optimizeThreshold(costMatrix, data, probationaryFraction):
  """Calcuate and return the optimal threshold.

  :param costMatrix: a dict containing the weights for true/false
      positive/negative
  """
  anomalyWindows = _processWindows(data)

  numWindows = sum([len(windows) for _, windows in anomalyWindows.iteritems()])

  data = _processData(data, anomalyWindows, probationaryFraction)

  results = _computeThresholdScores(data, numWindows, costMatrix)
  print "Done, best result: ", results[0:5]
  return results
