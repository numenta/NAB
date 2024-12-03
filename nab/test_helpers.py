# Copyright 2014-2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import os
import pandas
try:
  import simplejson as json
except ImportError:
  import json

from nab.util import createPath, makeDirsExist



def writeCorpusLabel(labelsPath, labelWindows):
  """
  Create a CorpusLabel file.
  @param labelsPath   (string)  Path to store the corpus label data.
  @param labelWindows (dict)    Dictionary containing key value pairs of
                                a relative path and its corresponding list of
                                windows.
  """
  createPath(labelsPath)
  windows = json.dumps(labelWindows,
    sort_keys=True, indent=4, separators=(',', ': '))

  with open(labelsPath, "w") as windowWriter:
    windowWriter.write(windows)


def writeCorpus(corpusDir, corpusData):
  """
  Create a corpus directory.
  @param corpusDir   (string)   Directory to store the corpus data files.
  @param corpusData   (dict)    Dictionary containing key value pairs of
                                a relative path and its corresponding data file
                                data (as a pandas.DataFrame).
  """
  makeDirsExist(corpusDir)

  for relativePath, data in corpusData.items():
    dataFilePath = os.path.join(corpusDir, relativePath)
    createPath(dataFilePath)
    data.to_csv(dataFilePath, index=False)


def generateTimestamps(start, increment, length):
  """
  Return a pandas Series containing the specified list of timestamps.
  @param start      (datetime)    Start time
  @param increment  (timedelta)   Time increment
  @param length     (int)         Number of datetime objects
  """
  timestamps = pandas.Series([start])
  for i in range(length - 1):
    timestamps.loc[i + 1] = timestamps.loc[i] + increment
  return timestamps


def generateWindows(timestamps, numWindows, windowSize):
  """
  Returns a list of numWindows windows, where each window is a pair of
  timestamps. Each window contains windowSize intervals. The windows are roughly
  evenly spaced throughout the list of timestsamps.
  @param timestamps  (Series) Pandas Series containing list of timestamps.
  @param numWindows  (int)    Number of windows to return
  @param windowSize  (int)    Number of 'intervals' in each window. An interval
                              is the duration between the first two timestamps.
  """
  start = timestamps[0]
  delta = timestamps[1] - timestamps[0]
  diff = int(round((len(timestamps) - numWindows * windowSize) / float(numWindows + 1)))
  windows = []
  for i in range(numWindows):
    t1 = start + delta * diff * (i + 1) + (delta * windowSize * i)
    t2 = t1 + delta * (windowSize - 1)
    if not any(timestamps == t1) or not any(timestamps == t2):
      raise ValueError("You got the wrong times from the window generator")
    windows.append([t1, t2])

  return windows
