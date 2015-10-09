# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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
"""
Tests the score normalization scheme.
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
  root = os.path.dirname(os.path.realpath(__file__))
  labelPath = os.path.abspath(
    os.path.join(root, "..", "test_labels/labels.json"))

  testRunner = Runner(dataDir=None,
                      resultsDir=resultsDir,
                      labelPath=labelPath,
                      profilesPath=None,
                      thresholdPath=None)

  testRunner.profiles = {
    profileName: {
      "CostMatrix": {
        "tpWeight": 1.0
      }
    }
  }

  if resultsName is not None:
    resultsFile = resultsName+'_'+profileName+'_scores.csv'
    resultsFilePath = os.path.join(resultsDir, resultsName, resultsFile)
    testRunner.resultsFiles = [resultsFilePath]

  return testRunner



class NormalizationTest(unittest.TestCase):

  def setUp(self):
    self._tmpDirs = []
    self.resultsHeaders = ['Detector','Profile','Score']


  def tearDown(self):
    for tmpDir in self._tmpDirs:
      shutil.rmtree(tmpDir)


  def _createTemporaryResultsDir(self):
    tmpResultsDir = tempfile.mkdtemp()
    self._tmpDirs.append(tmpResultsDir)
    return tmpResultsDir


  def testNullScoreLoading(self):
    """Tests that we fail apropriately if null detector scores are absent."""

    testRunner = Runner(dataDir=None,
                        resultsDir='',
                        labelPath=None,
                        profilesPath=None,
                        thresholdPath=None)

    # Should fail due to resultsDir/null not being a directory.
    with self.assertRaises(IOError):
      testRunner.normalize()

    tmpResultsDir = self._createTemporaryResultsDir()
    os.makedirs(os.path.join(tmpResultsDir,'null'))

    testRunner2 = createRunner(tmpResultsDir, 'standard')

    # Should fail due to resultsDir/null being empty.
    with self.assertRaises(IOError):
      testRunner2.normalize()


  def testResultsUpdate(self):
    """Tests that scores are correctly updated in final_results.json."""

    tmpResultsDir = self._createTemporaryResultsDir()
    os.makedirs(os.path.join(tmpResultsDir,'null'))
    os.makedirs(os.path.join(tmpResultsDir,'fake'))
    finalResults = os.path.join(tmpResultsDir, "final_results.json")

    self.assertFalse(os.path.exists(finalResults),
      "final_results.json already exists in temporary directory")

    # Create the null detector score file
    nullFile = 'null/null_standard_scores.csv'
    nullRow = ['null','standard','0.0']
    nullData = [self.resultsHeaders, nullRow]
    createCSV(tmpResultsDir, nullFile, nullData)

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
    os.makedirs(os.path.join(tmpResultsDir,'null'))
    os.makedirs(os.path.join(tmpResultsDir,'fake'))
    finalResults = os.path.join(tmpResultsDir, "final_results.json")

    self.assertFalse(os.path.exists(finalResults),
      "final_results.json already exists in temporary directory")

    # Create the null dtector score file
    nullFile = 'null/null_standard_scores.csv'
    nullRow = ['null','standard','-5.0']
    nullData = [self.resultsHeaders, nullRow]
    createCSV(tmpResultsDir, nullFile, nullData)

    # Create the fake results file
    fakeFile = 'fake/fake_standard_scores.csv'
    fakeRow = ['fake','standard','2.0']
    fakeData = [self.resultsHeaders, fakeRow]
    createCSV(tmpResultsDir, fakeFile, fakeData)

    testRunner = createRunner(tmpResultsDir, 'standard', 'fake')
    testRunner.normalize()

    # Check that scores have been properly normalized.
    with open(finalResults) as finalResultsFile:
      resultsDict = json.load(finalResultsFile)
      score = resultsDict['fake']['standard']

      self.assertEqual(score, 70.0,
        "normalized score of %f is not the expected 10.0" % score)



if __name__ == '__main__':
  unittest.main()
