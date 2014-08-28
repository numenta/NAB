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


import os
import datetime
import dateutil
import sys

def relativeFilePaths(directory):
  for dirpath,_,filenames in os.walk(directory):
    filenames = [f for f in filenames if not f[0] == "."]
    for f in filenames:
      yield os.path.join(dirpath, f)


def absoluteFilePaths(directory):
  for dirpath,_,filenames in os.walk(directory):
    filenames = [f for f in filenames if not f[0] == "."]
    for f in filenames:
      yield os.path.abspath(os.path.join(dirpath, f))

def makeDirsExist(dirname):
  """
  Makes sure a given path exists
  """

  if not os.path.exists(dirname):
    # This is being run in parralel so watch out for race condition.
    try:
      os.makedirs(dirname)
    except OSError:
      pass


def createPath(path):
  dirname = os.path.dirname(path)
  makeDirsExist(dirname)


def detectorClassToName(obj):
  name = obj.__name__[:-8].lower()
  return name

def detectorNameToClass(name):
  name = name[0].upper() + name[1:]
  className = name + "Detector"

  return className


def osPathSplit(path, debug=False):
  """
  os_path_split_asunder
  http://stackoverflow.com/questions/4579908/cross-platform-splitting-of-path-in-python
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
  for key in dictionary.keys():
    concat = head + "/" + key if head != "" else key
    if type(dictionary[key]) is dict:
      flattenDict(dictionary[key], files, concat)
    else:
      files[concat] = dictionary[key]

  return files

def strf(t):
  return datetime.datetime.strftime(t, "%Y-%m-%d %H:%M:%S.%f")

def strp(t):
  return dateutil.parser.parse(t)

def recur(function, value, n):
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
    """Deeply applies f across the datum."""
    if type(datum) == list:
        return [deepmap(f, x) for x in datum]
    else:
        return f(datum)

