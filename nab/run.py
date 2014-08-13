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
from optparse import OptionParser

from nab.lib.running import Runner


def main(options):
  root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
  runner = Runner(root, options)
  print 'got here'

  if options.detect:
    runner.getAlerts()

  elif options.score:
    runner.getScores()


if __name__ == "__main__":

  parser = OptionParser()

  parser.add_option("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus.")

  parser.add_option("--labelDir",
                    default="labels",
                    help="This holds all the label windows for the corpus.")

  parser.add_option("-r", "--detect",
                    help="Generate detector results but do not analyze results \
                    files.",
                    dest="detect",
                    default=False,
                    action="store_true")

  parser.add_option("-a", "--score",
                    help="Analyze results in the results directory",
                    dest="score",
                    default=False,
                    action="store_true")

  parser.add_option("-c", "--config",
                    default="config/benchmark_config.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_option("-p", "--profiles",
                    default="config/user_profiles.yaml",
                    help="The configuration file to use while running the "
                    "benchmark.")

  parser.add_option("--numCPUs",
                    help="The number of CPUs to use to run the "
                    "benchmark. If not specified all CPUs will be used.")

  parser.add_option("--plot",
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

  options, args = parser.parse_args()

  main(options)
