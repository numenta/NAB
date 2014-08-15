import os
import datetime
import dateutil
import sys

def absoluteFilePaths(directory):
  for dirpath,_,filenames in os.walk(directory):
    filenames = [f for f in filenames if not f[0] == '.']
    for f in filenames:
      yield os.path.abspath(os.path.join(dirpath, f))

def createPath(path):
  dirname = os.path.dirname(path)
  if not os.path.exists(dirname):
    os.makedirs(dirname)

def getDetectorClassName(detector):
  # If the detector is 'detector', the detector class must be named
    # DetectorDetector# If the detector is 'detector', the detector class must be named
  detector = detector[0].upper() + detector[1:]

  className = detector + "Detector"

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
  path = path.split('/')
  detector = path[0]
  path = path[1:]
  path.remove('alerts')

  filename = path[-1]
  toRemove = detector + '_alerts_'

  i = filename.index(toRemove)
  filename = filename[:i] + filename[i+len(toRemove):]

  path[-1] = filename
  path = '/'.join(path)
  # print path
  return path

def flattenDict(dictionary, files={}, head=''):
  for key in dictionary.keys():
    concat = head + '/' + key if head != '' else key
    if type(dictionary[key]) is dict:
      flattenDict(dictionary[key], files, concat)
    else:
      files[concat] = dictionary[key]

  return files

def strf(t):
  return datetime.datetime.strftime(t, '%Y-%m-%d %H:%M:%S.%f')

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

