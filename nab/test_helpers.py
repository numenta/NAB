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
