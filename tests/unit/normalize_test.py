# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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
"""
Tests normalization scheme for normalizing detectors' scores according
to baseline.
"""

import csv
import os
import shutil
import tempfile
import unittest
try:
  import simplejson as json
except ImportError:
  import json

from nab.runner import Runner


def createCSV(parentDir, fileName, data):
  """
  Write a CSV file for testing.

  @param parentDir      (str)             a directory path
  @param fileName       (str)             name of file
  @param data           (list)            list of lists to write to CSV
  """
  filePath = os.path.join(parentDir, fileName)

  with open(filePath, 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',')
    for ln in data:
      filewriter.writerow(ln)

  return filePath


def createRunner(resultsDir, profileName, resultsName=None):
  """Create a nab.runner.Runner object for testing."""
  testRunner = Runner(dataDir=None,
                      resultsDir=resultsDir,
                      labelPath=None,
                      profilesPath=None,
                      thresholdPath=None)

  testRunner.profiles = json.loads('{"'+profileName+'": {}}')

  if resultsName is not None:
    resultsFile = resultsName+'_'+profileName+'_scores.csv'
    resultsFilePath = os.path.join(resultsDir, resultsName, resultsFile)
    testRunner.resultsFiles = [resultsFilePath]

  return testRunner



class NormalizationTest(unittest.TestCase):

  def setUp(self):
    self.tmpDir = None
    self.resultsHeaders = ['Detector','Profile','Score']


  def tearDown(self):
    if self.tmpDir is not None:
      shutil.rmtree(self.tmpDir)


  def _createTemporaryResultsDir(self):
    tmpResultsDir = tempfile.mkdtemp()
    self.tmpDir = tmpResultsDir
    return tmpResultsDir


  def testBaselineScoreLoading(self):
    """Tests that we fail apropriately if baseline scores are absent."""

    testRunner = Runner(dataDir=None,
                        resultsDir='',
                        labelPath=None,
                        profilesPath=None,
                        thresholdPath=None)

    # Should fail due to resultsDir/baseline not being a directory.
    with self.assertRaises(IOError):
      testRunner.normalize()

    tmpResultsDir = self._createTemporaryResultsDir()
    os.makedirs(os.path.join(tmpResultsDir,'baseline'))

    testRunner2 = createRunner(tmpResultsDir, 'standard')

    # Should fail due to resultsDir/baseline being empty.
    with self.assertRaises(IOError):
      testRunner2.normalize()


  def testResultsUpdate(self):
    """Tests that scores are correctly updated in final_results.json."""

    tmpResultsDir = self._createTemporaryResultsDir()
    os.makedirs(os.path.join(tmpResultsDir,'baseline'))
    os.makedirs(os.path.join(tmpResultsDir,'fake'))
    finalResults = os.path.join(tmpResultsDir, "final_results.json")

    self.assertFalse(os.path.exists(finalResults),
      "final_results.json already exists in temporary directory")

    # Create the baseline file
    baselineFile = 'baseline/baseline_standard_scores.csv'
    baselineRow = ['baseline','standard','0.0']
    baselineData = [self.resultsHeaders, baselineRow]
    createCSV(tmpResultsDir, baselineFile, baselineData)

    # Create the fake results file
    fakeFile = 'fake/fake_standard_scores.csv'
    fakeRow = ['fake','standard','1.0']
    fakeData = [self.resultsHeaders, fakeRow]
    createCSV(tmpResultsDir, fakeFile, fakeData)

    testRunner = createRunner(tmpResultsDir, 'standard', 'fake')
    testRunner.normalize()
    self.assertTrue(os.path.exists(finalResults),
      "final_results.json was not created during normalization.")


  def testScoreNormalization(self):
    """Tests that scores are properly normalized."""

    tmpResultsDir = self._createTemporaryResultsDir()
    os.makedirs(os.path.join(tmpResultsDir,'baseline'))
    os.makedirs(os.path.join(tmpResultsDir,'fake'))
    finalResults = os.path.join(tmpResultsDir, "final_results.json")

    self.assertFalse(os.path.exists(finalResults),
      "final_results.json already exists in temporary directory")

    # Create the baseline file
    baselineFile = 'baseline/baseline_standard_scores.csv'
    baselineRow = ['baseline','standard','4.0']
    baselineData = [self.resultsHeaders, baselineRow]
    createCSV(tmpResultsDir, baselineFile, baselineData)

    # Create the fake results file
    fakeFile = 'fake/fake_standard_scores.csv'
    fakeRow = ['fake','standard','8.0']
    fakeData = [self.resultsHeaders, fakeRow]
    createCSV(tmpResultsDir, fakeFile, fakeData)

    testRunner = createRunner(tmpResultsDir, 'standard', 'fake')
    testRunner.normalize()

    # Check that scores have been properly normalized.
    with open(finalResults) as finalResultsFile:
      resultsDict = json.load(finalResultsFile)
      score = resultsDict['fake']['standard']

      self.assertEqual(score, 10.0,
        "normalized score of %f is not the expected 10.0" % score)

if __name__ == '__main__':
  unittest.main()
