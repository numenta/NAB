# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
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

"""Tests scripts.create_new_detector for creating appropriate dirs and files."""

import os
import shutil
import simplejson as json
import unittest

from nab.util import recur
from scripts.create_new_detector import createResultsDir, createThresholds

depth = 3

root = recur(os.path.dirname, os.path.realpath(__file__), depth)

class NewDetectorTest(unittest.TestCase):

  def testCreateResultsDir(self):
    """Tests the creation of the appropriate results directory."""

    detector = "fake_test_detector"
    results_dir = os.path.join(root, "results")
    category_sub_dirs = ["fake_cat1", "fake_cat2"]

    self.assertFalse(detector in next(os.walk(results_dir))[1],
      "{0} is already in the results directory {1}".format(detector,
                                                           results_dir))

    createResultsDir(detector, results_dir, category_sub_dirs)

    self.assertTrue(detector in next(os.walk(results_dir))[1],
      "{0} was not created in the results directory {1}".format(detector,
                                                                results_dir))

    subdirs = next(os.walk(os.path.join(results_dir,detector)))[1]

    for subdir in category_sub_dirs:
      self.assertTrue(subdir in subdirs, "{0} was not created.".format(subdir))

    # Clean up
    shutil.rmtree(os.path.join(results_dir,detector))


  def testCreateThresholds(self):
    """Tests the addition of a thresholds entry in the given json file."""

    detector = "fake_test_detector"
    threshold_file = os.path.join(root, "config/thresholds.json")

    with open(threshold_file) as in_file:
      old_thresholds = json.load(in_file)

    self.assertFalse(detector in old_thresholds,
                     "{0} is already in the thresholds file.".format(detector))

    createThresholds(detector, threshold_file)

    with open(threshold_file) as in_file:
      new_thresholds = json.load(in_file)

      self.assertTrue(detector in new_thresholds,
                      "{0} not generated in thresholds file.".format(detector))

    # Clean up
    with open(threshold_file, "w") as out_file:
      out_file.write(json.dumps(old_thresholds,
                     sort_keys=True, indent=4, separators=(',', ': ')))


if __name__ == '__main__':
  unittest.main()
