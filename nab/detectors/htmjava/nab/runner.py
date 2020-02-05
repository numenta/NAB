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

import multiprocessing
import os
import pandas
try:
  import simplejson as json
except ImportError:
  import json

from nab.corpus import Corpus
from nab.detectors.base import detectDataSet
from nab.labeler import CorpusLabel


class Runner(object):
  """
Class to run detection on the NAB benchmark using the specified set of
profiles and/or detectors.
"""

  def __init__(self,
               dataDir,
               resultsDir,
               labelPath,
               profilesPath,
               numCPUs=None):
    """
    @param dataDir        (string)  Directory where all the raw datasets exist.

    @param resultsDir     (string)  Directory where the detector anomaly scores
                                    will be scored.

    @param labelPath      (string)  Path where the labels of the datasets
                                    exist.

    @param profilesPath   (string)  Path to JSON file containing application
                                    profiles and associated cost matrices.

    @param numCPUs        (int)     Number of CPUs to be used for calls to
                                    multiprocessing.pool.map
    """
    self.dataDir = dataDir
    self.resultsDir = resultsDir

    self.labelPath = labelPath
    self.profilesPath = profilesPath
    self.pool = multiprocessing.Pool(numCPUs)

    self.probationaryPercent = 0.15
    self.windowSize = 0.10

    self.corpus = None
    self.corpusLabel = None
    self.profiles = None


  def initialize(self):
    """Initialize all the relevant objects for the run."""
    self.corpus = Corpus(self.dataDir)
    self.corpusLabel = CorpusLabel(path=self.labelPath, corpus=self.corpus)

    with open(self.profilesPath) as p:
      self.profiles = json.load(p)


  def detect(self, detectors):
    """Generate results file given a dictionary of detector classes

    Function that takes a set of detectors and a corpus of data and creates a
    set of files storing the alerts and anomaly scores given by the detectors

    @param detectors     (dict)         Dictionary with key value pairs of a
                                        detector name and its corresponding
                                        class constructor.
    """
    print "\nRunning detection step"

    count = 0
    args = []
    for detectorName, detectorConstructor in detectors.iteritems():
      for relativePath, dataSet in self.corpus.dataFiles.iteritems():

        if self.corpusLabel.labels.has_key(relativePath):
          args.append(
            (
              count,
              detectorConstructor(
                dataSet=dataSet,
                probationaryPercent=self.probationaryPercent),
              detectorName,
              self.corpusLabel.labels[relativePath]["label"],
              self.resultsDir,
              relativePath
            )
          )

          count += 1

    # Using `map_async` instead of `map` so interrupts are properly handled.
    # See: http://stackoverflow.com/a/1408476
    self.pool.map_async(detectDataSet, args).get(999999)
