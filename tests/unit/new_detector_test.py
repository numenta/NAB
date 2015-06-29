# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
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

"""Tests scripts.create_new_detector for creating appropriate dirs and files."""

import shutil
import os
import unittest

try:
  import simplejson as json
except ImportError:
  import json

from scripts.create_new_detector import createResultsDir, createThresholds



class NewDetectorTest(unittest.TestCase):

  def testCreateResultsDir(self):
    """Tests the creation of the appropriate results directory."""

    detector = "fake_test_detector"
    results_dir = "../../results/"
    category_sub_dirs = ["fake_cat1", "fake_cat2"]

    self.assertFalse(detector in next(os.walk(results_dir))[1],
      detector+" is already in the results directory "+results_dir)

    createResultsDir(detector, results_dir, category_sub_dirs)

    self.assertTrue(detector in next(os.walk(results_dir))[1],
      detector+" was not created in the results directory "+results_dir)

    subdirs = next(os.walk(results_dir+detector))[1]

    for subdir in category_sub_dirs:
      self.assertTrue(subdir in subdirs, subdir+" was not created.")

    # Clean up
    shutil.rmtree(results_dir+detector)


  def testCreateThresholds(self):
    """Tests the addition of a thresholds entry in the given json file."""

    detector = "fake_test_detector"
    threshold_file = "../../config/thresholds.json"

    with open(threshold_file) as in_file:
      old_thresholds = json.load(in_file)

    self.assertFalse(detector in old_thresholds,
                     detector+" is already in the thresholds file.")

    createThresholds(detector, threshold_file)

    with open(threshold_file) as in_file:
      new_thresholds = json.load(in_file)

      self.assertTrue(detector in new_thresholds,
                      detector+" was not generated in the thresholds file.")

    # Clean up
    with open(threshold_file, "w") as out_file:
      out_file.write(json.dumps(old_thresholds,
                     sort_keys=True, indent=4, separators=(',', ': ')))


if __name__ == '__main__':
  unittest.main()
