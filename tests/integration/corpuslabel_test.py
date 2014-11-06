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
import json
import shutil
import pandas
import datetime
import unittest2 as unittest

import nab.corpus
import nab.labeler

from nab.util import recur, createPath, makeDirsExist, strp

from nab.test_helpers import generateTimestamps


def writeCorpusLabel(labelsPath, labelWindows):
  createPath(labelsPath)
  windows = json.dumps(labelWindows,
    sort_keys=True, indent=4, separators=(',', ': '))

  with open(labelsPath, "w") as windowWriter:
    windowWriter.write(windows)


def writeCorpus(corpusPath, corpusData):
  makeDirsExist(corpusPath)

  for relativePath, data in corpusData.iteritems():
    dataFilePath = os.path.join(corpusPath, relativePath)
    createPath(dataFilePath)
    data.to_csv(dataFilePath, index=False)



class CorpusLabelTest(unittest.TestCase):


  @classmethod
  def setUpClass(cls):
    depth = 3

    cls.root = recur(os.path.dirname, os.path.realpath(__file__), depth)
    cls.corpusSrc = os.path.join(cls.root, "tests/test_data")


    cls.labelsFile = os.path.join(cls.root,
      "tests/test_labels/test_ground_truth.json")

    cls.corpus = nab.corpus.Corpus(cls.corpusSrc)

    cls.tempDir = os.path.join(cls.root, "tests/tmp")

    cls.tmpCorpusPath = os.path.join(cls.tempDir, "data")
    cls.tmpCorpusLabelPath = os.path.join(cls.tempDir, "labels/label.json")


  def setUp(self):
    makeDirsExist(self.tempDir)

    self.corpusLabels = nab.labeler.CorpusLabel(self.labelsFile, self.corpus)


  def tearDown(self):
    shutil.rmtree(self.tempDir)


  def test_throwErrorWhenTimestampsNotInDataFile(self):
    relativePath = "throwErrorWhenTimestampNotInDataFileTest.csv"

    data = pandas.DataFrame({'timestamp' :
      generateTimestamps(strp("2014-01-01 00:00:00.0000"), None, 1)})

    writeCorpus(self.tmpCorpusPath, {relativePath : data})

    window = ["2015-01-01 00:00:00.00000",
      "2015-01-01 00:00:00.00000"]

    writeCorpusLabel(self.tmpCorpusLabelPath, {relativePath: [window]})

    corpus = nab.corpus.Corpus(self.tmpCorpusPath)

    exceptionRaised = False

    try:
      nab.labeler.CorpusLabel(self.tmpCorpusLabelPath, corpus)

    except ValueError:
      exceptionRaised = True

    self.assertTrue(exceptionRaised)


  def test_throwErrorWhenOverLappingWindows(self):
    relativePath = "throwErrorWhenTimestampsCreateOverLappingWindows.csv"

    timestamps = generateTimestamps(strp("2014-01-01 00:00:00.0000"),
      datetime.timedelta(minutes=5), 10)
    data = pandas.DataFrame({'timestamp' : timestamps})

    writeCorpus(self.tmpCorpusPath, {relativePath : data})

    windows = [["2014-01-01 00:00:00.00000", "2014-01-01 00:10:00.00000"],
    ["2014-01-01 00:05:00.00000", "2014-01-01 00:15:00.00000"]]

    writeCorpusLabel(self.tmpCorpusLabelPath, {relativePath: windows})

    corpus = nab.corpus.Corpus(self.tmpCorpusPath)

    exceptionRaised = False

    try:
      nab.labeler.CorpusLabel(self.tmpCorpusLabelPath, corpus)

    except ValueError:
      exceptionRaised = True

    self.assertTrue(exceptionRaised)


  def test_throwErrorWindowStartTimeIsLaterThanWindowEndTime(self):
    relativePath = "throwErrorWindowStartTimeIsLaterThanWindowEndTime.csv"

    timestamps = generateTimestamps(strp("2014-01-01 00:00:00.0000"), None, 1)
    data = pandas.DataFrame({'timestamp' : timestamps})

    writeCorpus(self.tmpCorpusPath, {relativePath : data})

    window = ["2014-01-01 00:05:00.00000",
      "2014-01-01 00:00:00.00000"]

    writeCorpusLabel(self.tmpCorpusLabelPath, {relativePath: [window]})

    corpus = nab.corpus.Corpus(self.tmpCorpusPath)

    exceptionRaised = False

    try:
      nab.labeler.CorpusLabel(self.tmpCorpusLabelPath, corpus)

    except ValueError:
      exceptionRaised = True

    self.assertTrue(exceptionRaised)


  # def test_allRowsLabeledAnomalousShouldBeWithinExactlyOneWindow(self):
  #   pass


  # def test_showWarningWhenDataFilesDontHaveCorrespondingLabelsEntries(self):
  #   pass


  # def test_throwErrorWhenThereIsLabelForNonExistentDataFile(self):
  #   pass



if __name__ == '__main__':
  unittest.main()