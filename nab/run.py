#!/usr/bin/env python
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
import yaml
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/lib')



import multiprocessing

from lib.corpus import Corpus
from lib.score import Scorer
from lib.util import (getDetectorClassName, convertResultsPathToDataPath)
from lib.label import CorpusLabel

from optparse import OptionParser

from detectors import (NumentaDetector, SkylineDetector)

from collections import defaultdict
import pandas
import math


sys.path.append(os.path.dirname(os.path.realpath(__file__)))


if __name__ == "__main__":

  parser = OptionParser()
  parser.add_option("-a", "--analyzeOnly",
                    help="Analyze results in the results directory only.",
                    dest="analyzeOnly",
                    default=False,
                    action="store_true")

  parser.add_option("-r", "--resultsOnly",
                    help="Generate detector results but do not analyze results \
                    files.",
                    dest="resultsOnly",
                    default=False,
                    action="store_true")

  parser.add_option("-p", "--plot",
                    help="If you have Plotly installed "
                    "this option will plot results and ROC curves for each \
                    dataset.",
                    dest="plotResults",
                    default=False,
                    action="store_true")

  parser.add_option("-v", "--verbosity",
                    default=0,
                    help="Increase the amount and detail of output by setting \
                    this greater than 0.")

  parser.add_option("-c", "--config",
                    default="scripts/config/benchmark_config.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_option("--profiles",
                    default="scripts/config/user_profiles.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_option("--numCPUs",
                    help="The number of CPUs to use to run the "
                    "benchmark. If not specified all CPUs will be used.")

  parser.add_option("--labelDir",
                    default="labels",
                    help="This holds all the label windows for the corpus.")

  parser.add_option("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus.")


  options, args = parser.parse_args()

  Runner(options)
