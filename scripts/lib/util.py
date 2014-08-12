import os

def absoluteFilePaths(directory):
  for dirpath,_,filenames in os.walk(directory):
    filenames = [f for f in filenames if not f[0] == '.']
    for f in filenames:
      yield os.path.abspath(os.path.join(dirpath, f))

def createPath(path):
  dirname = os.path.dirname(path)
  if not os.path.exists(dirname):
    os.makedirs(dirname)