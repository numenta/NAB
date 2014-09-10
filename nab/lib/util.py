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

"""
"""

import os
import datetime
import dateutil
import sys
import pprint

def checkInputs(args):
  pprint.pprint(vars(args))
  return input("Enter 1 to proceed, 0 otherwise: ")


def relativeFilePaths(directory):
  """
  Given directory, gets the path of all files within relative to the directory.

  @param directory  (string)      Absolute directory name.

  @return           (iterable)    All filepaths within directory, relative to
                                  that directory.
  """
  for dirpath,_,filenames in os.walk(directory):
    filenames = [f for f in filenames if not f[0] == "."]
    for f in filenames:
      yield os.path.join(dirpath, f)


def absoluteFilePaths(directory):
  """
  Given directory, gets the absolute path of all files within.

  @param  directory   (string)    Directory name.

  @return             (iterable)  All absolute filepaths within directory.
  """
  for dirpath,_,filenames in os.walk(directory):
    filenames = [f for f in filenames if not f[0] == "."]
    for f in filenames:
      yield os.path.abspath(os.path.join(dirpath, f))

def makeDirsExist(dirname):
  """
  Makes sure a given directory exists. If not, it creates it.

  @param dirname  (string)  Absolute directory name.
  """

  if not os.path.exists(dirname):
    # This is being run in parralel so watch out for race condition.
    try:
      os.makedirs(dirname)
    except OSError:
      pass


def createPath(path):
  """
  Makes sure a given path exists. If not, it creates it.

  @param path   (string) Absolute path name.
  """
  dirname = os.path.dirname(path)
  makeDirsExist(dirname)


def detectorClassToName(obj):
  """
  Removes the 'detector' from the end of detector class's name.

  @param obj  (subclass of AnomalyDetector)   Detector class.

  @return     (string)                        Name of detector.
  """
  tailLength = len('detector')
  name = obj.__name__[:-tailLength].lower()
  return name

def detectorNameToClass(name):
  """
  """
  name = name[0].upper() + name[1:]
  className = name + "Detector"

  return className


def osPathSplit(path, debug=False):
  """
  os_path_split_asunder
  http://stackoverflow.com/questions/4579908/cross-platform-splitting-of-path-in-python
  Path splitter that works on both unix-based and windows platforms.

  @param path (string) Path to be split.

  @return     (list)   Split path.
  """
  parts = []
  while True:
    newpath, tail = os.path.split(path)
    if debug:
      print repr(path), (newpath, tail)
    if newpath == path:
      assert not tail
      if path:
        parts.append(path)
      break
    parts.append(tail)
    path = newpath
  parts.reverse()
  return parts

def convertResultsPathToDataPath(path):
  """
  @param path (string)  Path to dataset in the data directory.

  @return     (string)  Path to dataset result in the result directory.
  """
  # print path
  path = path.split("/")
  detector = path[0]
  path = path[1:]

  filename = path[-1]
  toRemove = detector + "_"

  i = filename.index(toRemove)
  filename = filename[:i] + filename[i+len(toRemove):]

  path[-1] = filename
  path = "/".join(path)
  # print path
  return path

def flattenDict(dictionary, files={}, head=""):
  """
  @param dictionary (dict)    Dictionary of dictionaries to be flattened.

  @param files      (dict)    Dictionary to build up

  @param head       (string)  Prefix to each key
  """
  for key in dictionary.keys():
    concat = head + "/" + key if head != "" else key
    if type(dictionary[key]) is dict:
      flattenDict(dictionary[key], files, concat)
    else:
      files[concat] = dictionary[key]

  return files

def strf(t):
  """
  @param t  (datetime.Datetime) Datetime object.

  @return   (string)            Formatted string of datetime.
  """
  return datetime.datetime.strftime(t, "%Y-%m-%d %H:%M:%S.%f")

def strp(t):
  """
  @param t (datetime.datetime)  String of datetime with format:
                                "YYYY-MM-DD HH:mm:SS.ss".

  @return   (string)            Datetime object.
  """
  return dateutil.parser.parse(t)

def recur(function, value, n):
  """
  @param function (function)    Function to recurse.

  @param value    (value)       Value to recurse on.

  @param n        (int)         Number of times to recurse.
  """
  if n < 0 or int(n) != n:
    print "incorrect input"
    sys.exit()

  elif n == 0:
    return value

  elif n == 1:
    return function(value)

  else:
    return recur(function, function(value), n-1)

def deepmap(f, datum):
  """
  Deeply applies f across the datum.

  @param f      (function)    Function to map with.

  @param datum  (datum)       Object to map over.
  """
  if type(datum) == list:
      return [deepmap(f, x) for x in datum]
  else:
      return f(datum)

