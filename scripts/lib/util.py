import os
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
  if className not in globals():
    print("ERROR: The provided detector was not recognized. Please add a class "
          "in the detectors/ dir. Add that class to the detectors/__init__.py "
          "file and finally add that class to the list of detectors imported "
          "in this file. ... Sorry!")
    sys.exit(1)
  else:
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
  return path
