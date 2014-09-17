import os
from setuptools import setup, find_packages
from nab.lib.util import relativeFilePaths, recur
import csv

# Utility function to read the README file.
# Used for the long_description.  It"s nice, because now 1) we have a top level
# README file and 2) it"s easier to type in the README file than to put a raw
# string in below ...
def read(fname):
  with open(os.path.join(os.path.dirname(__file__), fname)) as f:
    result = f.read()
  return result

depth = 1

root = recur(os.path.dirname, os.path.realpath(__file__), depth)

def writePaths(folderName):
  with open(os.path.join(root, folderName + "_file_paths.txt"), "w") as f:
    paths = relativeFilePaths(os.path.join(root, folderName))
    paths = map((lambda x: [str(x).replace(root + "/", "")]), paths)

    writer = csv.writer(f)
    writer.writerows(paths)

# with open(os.path.join(root,"data_file_paths.txt"), "w") as f:
#   paths = relativeFilePaths(os.path.join(root,"data"))
#   writer = csv.writer(f)
#   writer.writerows(paths)
#   # print >> f, "[" + ",\n".join("\""+str(p).replace(root + "/", "")+"\"" for p in paths) + "];"

# with open(os.path.join(root,"results_file_paths.txt"), "w") as f:
#   paths = relativeFilePaths(os.path.join(root,"results"))

#   # writer = csv.writer(f)
#   # writer.writerows(paths)

#   # print >> f, "[" + ",\n".join("\""+str(p).replace(root + "/", "")+"\"" for p in paths) + "];"

writePaths("data")
writePaths("results")

setup(
  name = "nab",
  version = "0.1",
  author = "Jay Gokhale",
  author_email = "jgokhale@numenta.com",
  description = (
    "Numenta Anomaly Benchmark: A benchmark for streaming \anomaly prediction"),
  license = "GPL",
  packages=find_packages(),
  long_description=read("README.md"),
)

