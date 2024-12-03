# Copyright 2014-2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import os
import pkg_resources
import warnings
from setuptools import setup, find_packages

REPO_DIR = os.path.dirname(os.path.realpath(__file__))



# Utility function to read the README file.
# Used for the long_description.  It"s nice, because now 1) we have a top level
# README file and 2) it"s easier to type in the README file than to put a raw
# string in below ...
def read(fname):
  with open(os.path.join(os.path.dirname(__file__), fname)) as f:
    result = f.read()
  return result



def nupicInstalled():
  """
  Determine whether NuPIC is already installed.
   :return: boolean
  """
  try:
    _ = pkg_resources.get_distribution("nupic")
    return True
  except pkg_resources.DistributionNotFound:
    pass  # Silently ignore. NuPIC will be installed later.

  return False



def parseFile(requirementFile):
  """
  Parse requirement file.
  :return: list of requirements.
  """
  try:
    return [
      line.strip()
      for line in open(requirementFile).readlines()
      if not line.startswith("#")
    ]
  except IOError:
    return []



def findRequirements():
  """
  Read the requirements.txt file and parse into requirements for setup's
  install_requirements option.
  """
  requirementsPath = os.path.join(REPO_DIR, "requirements.txt")
  requirements = parseFile(requirementsPath)

  if nupicInstalled():
    # The user already has a version of NuPIC installed. We'll remove the entry
    # in requirements.txt to not conflate the two and will issue a user warning.
    reqs = []
    for req in requirements:
      if "nupic" != req.split("==")[0]:
        reqs.append(req)
      else:
        warnings.warn("NuPIC is already installed so %s from requirements.txt "
                      "will be not be installed." % req)
  else:
    reqs = requirements
  return reqs



if __name__ == "__main__":
  requirements = findRequirements()

  setup(
    name="nab",
    version="1.0",
    author="Alexander Lavin",
    author_email="nab@numenta.org",
    description=(
      "Numenta Anomaly Benchmark: A benchmark for streaming anomaly prediction"),
    license="AGPL",
    packages=find_packages(),
    long_description=read("README.md"),
    install_requires=requirements,
    entry_points={
      "console_scripts": [
        "nab-plot = nab.plot:main",
      ],
    },
  )
