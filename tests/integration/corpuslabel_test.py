# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
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
import shutil
import pandas
import tempfile
import datetime
import unittest2 as unittest

import nab.corpus
import nab.labeler
from nab.util import strp
from nab.test_helpers import writeCorpus, writeCorpusLabel, generateTimestamps



class CorpusLabelTest(unittest.TestCase):

  def setUp(self):
    self.tempDir = os.path.join(tempfile.mkdtemp(), "test")
    self.tempCorpusPath = os.path.join(self.tempDir, "data")
    self.tempCorpusLabelPath = os.path.join(
      self.tempDir, "labels", "label.json")


  def tearDown(self):
    shutil.rmtree(self.tempDir)


  def test_throwErrorWhenWindowTimestampsNotInDataFile(self):
    """
    Test whether a value error is thrown when label windows contain timestamps
    that do no exist in the date file.
    """
    data = pandas.DataFrame({'timestamp' :
      generateTimestamps(strp("2014-01-01"), None, 1)})

    windows = [["2015-01-01", "2015-01-01"]]

    writeCorpus(self.tempCorpusPath, {"test_data_file.csv" : data})
    writeCorpusLabel(self.tempCorpusLabelPath, {"test_data_file.csv": windows})

    corpus = nab.corpus.Corpus(self.tempCorpusPath)

    self.assertRaises(ValueError, nab.labeler.CorpusLabel,
      self.tempCorpusLabelPath, corpus)


  def test_throwErrorWhenOverLappingWindows(self):
    """
    Test whether a value error is thrown when there is an overlap between two
    label windows for the same data file.
    """
    data = pandas.DataFrame({'timestamp' :
      generateTimestamps(strp("2014-01-01"),
      datetime.timedelta(minutes=5), 10)})

    windows = [["2014-01-01 00:00", "2014-01-01 00:10"],
      ["2014-01-01 00:05", "2014-01-01 00:15"]]

    writeCorpus(self.tempCorpusPath, {"test_data_file.csv" : data})
    writeCorpusLabel(self.tempCorpusLabelPath, {"test_data_file.csv": windows})

    corpus = nab.corpus.Corpus(self.tempCorpusPath)

    self.assertRaises(ValueError, nab.labeler.CorpusLabel,
      self.tempCorpusLabelPath, corpus)


  def test_throwErrorWindowStartTimeIsLaterThanWindowEndTime(self):
    """
    Test whether a value error is thrown when a label window's start and end
    times are not in chronological order.
    """
    data = pandas.DataFrame({'timestamp' :
      generateTimestamps(strp("2014-01-01"), None, 1)})

    windows = [["2014-01-01 00:05", "2014-01-01 00:00"]]

    writeCorpus(self.tempCorpusPath, {"test_data_file.csv" : data})
    writeCorpusLabel(self.tempCorpusLabelPath, {"test_data_file.csv": windows})

    corpus = nab.corpus.Corpus(self.tempCorpusPath)

    self.assertRaises(ValueError, nab.labeler.CorpusLabel,
      self.tempCorpusLabelPath, corpus)


  def test_allRowsLabeledAnomalousShouldBeWithinAWindow(self):
    """
    Test whether all timestamps labeled as anomalous are within a label window.
    """
    data = pandas.DataFrame({'timestamp' :
      generateTimestamps(strp("2014-01-01"),
      datetime.timedelta(minutes=5), 10)})

    windows = [["2014-01-01 00:15", "2014-01-01 00:30"]]

    writeCorpus(self.tempCorpusPath, {"test_data_file.csv": data})
    writeCorpusLabel(self.tempCorpusLabelPath, {"test_data_file.csv": windows})

    corpus = nab.corpus.Corpus(self.tempCorpusPath)

    corpusLabel = nab.labeler.CorpusLabel(self.tempCorpusLabelPath, corpus)

    for relativePath, l in corpusLabel.labels.iteritems():
      windows = corpusLabel.windows[relativePath]

      for row in l[l["label"] == 1].iterrows():
        self.assertTrue(
          any([w[0] <= row[1]["timestamp"] <= w[1] for w in windows]))


  def test_throwErrorWhenThereIsLabelForNonExistentDataFile(self):
    """
    Test whether a key error is thrown when there are labels for a data file
    that doesn't exist in the corpus.
    """
    data = pandas.DataFrame({'timestamp' :
      generateTimestamps(strp("2014-01-01"),
      datetime.timedelta(minutes=5), 10)})

    windows = [["2014-01-01 00:15", "2014-01-01 00:30"]]

    writeCorpus(self.tempCorpusPath, {"test_data_file.csv": data})
    writeCorpusLabel(self.tempCorpusLabelPath, {
      "test_data_file.csv": windows, "non_existent_data_file.csv": windows})

    corpus = nab.corpus.Corpus(self.tempCorpusPath)

    self.assertRaises(KeyError, nab.labeler.CorpusLabel,
      self.tempCorpusLabelPath, corpus)


  def test_showWarningWhenDataFilesDontHaveCorrespondingLabelsEntries(self):
    """
    Test whether a warning is raised when there there is data file that doesn't
    have a corresponding list of label windows.
    """
    data = pandas.DataFrame({'timestamp' :
      generateTimestamps(strp("2014-01-01"),
      datetime.timedelta(minutes=5), 10)})

    windows = [["2014-01-01 00:15", "2014-01-01 00:30"]]

    writeCorpus(self.tempCorpusPath, {"test_data_file1.csv": data,
      "test_data_file2.csv": data})
    writeCorpusLabel(self.tempCorpusLabelPath, {"test_data_file1.csv": windows})

    corpus = nab.corpus.Corpus(self.tempCorpusPath)

    self.assertRaisesRegexp(KeyError, "Valid data file within corpus does not "
    "have a corresponding label entry", nab.labeler.CorpusLabel,
      self.tempCorpusLabelPath, corpus)



if __name__ == '__main__':
  unittest.main()
