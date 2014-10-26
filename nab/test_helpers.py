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

import pandas


def generateTimestamps(start, increment, length):
  """
  Return a pandas Series containing the specified list of timestamps.

  @param start      (datetime)    Start time
  @param increment  (timedelta)   Time increment
  @param length     (int)         Number of datetime objects
  """
  timestamps = pandas.Series([start])
  for i in xrange(length - 1):
    timestamps.loc[i + 1] = timestamps.loc[i] + increment
  return timestamps


def generateWindows(timestamps, numWindows, windowSize):
  start = timestamps[0]
  delta = timestamps[1] - timestamps[0]
  length = len(timestamps)
  diff = int(round((length - numWindows * windowSize) / float(numWindows + 1)))
  windows = []
  for i in xrange(numWindows):
    t1 = start + delta * diff * (i + 1) + (delta * windowSize * i)
    t2 = t1 + (delta) * (windowSize - 1)
    if not any(timestamps == t1) or not any(timestamps == t2):
      raise ValueError("You got the wrong times from the window generator")
    windows.append([t1, t2])
  return windows


def generateLabels(timestamps, windows):
  labels = pandas.Series([0]*len(timestamps))
  for t1, t2 in windows:
    subset = timestamps[timestamps >= t1][timestamps <= t2]
    indices = subset.loc[:].index
    labels.values[indices] = 1
  return labels


