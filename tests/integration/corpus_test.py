# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

import copy
import numpy as np
import os
import pandas
import shutil
import tempfile
import unittest

import nab.corpus
from nab.util import recur



class CorpusTest(unittest.TestCase):


  @classmethod
  def setUpClass(cls):
    depth = 3

    cls.root = recur(os.path.dirname, os.path.realpath(__file__), depth)
    cls.corpusSource = os.path.join(cls.root, "tests", "test_data")


  def setUp(self):
    self.corpus = nab.corpus.Corpus(self.corpusSource)


  def testGetDataFiles(self):
    """
    Test the getDataFiles() function, specifically check if corpus.dataFiles
    is a dictionary containing DataFile objects containing pandas.DataFrame
    objects to represent the underlying data.
    """
    for df in list(self.corpus.dataFiles.values()):
      self.assertIsInstance(df, nab.corpus.DataFile)
      self.assertIsInstance(df.data, pandas.DataFrame)
      self.assertEqual(set(df.data.columns.values),
        set(["timestamp", "value"]))


  def testAddColumn(self):
    """
    Test the addColumn() function, specificially check if a new column named
    "test" is added.
    """
    columnData = {}
    for relativePath, df in self.corpus.dataFiles.items():
      rows, _ = df.data.shape
      columnData[relativePath] = pandas.Series(np.zeros(rows))

    self.corpus.addColumn("test", columnData, write=False)

    for df in list(self.corpus.dataFiles.values()):
      self.assertEqual(set(df.data.columns.values),
        set(["timestamp", "value", "test"]))


  def testRemoveColumn(self):
    """
    Test the removeColumn() function, specifically check if an added column
    named "test" is removed.
    """
    columnData = {}
    for relativePath, df in self.corpus.dataFiles.items():
      rows, _ = df.data.shape
      columnData[relativePath] = pandas.Series(np.zeros(rows))

    self.corpus.addColumn("test", columnData, write=False)

    self.corpus.removeColumn("test", write=False)

    for df in list(self.corpus.dataFiles.values()):
      self.assertEqual(set(df.data.columns.values),
        set(["timestamp", "value"]))


  def testCopy(self):
    """
    Test the copy() function, specifically check if it copies the whole corpus
    to another directory and that the copied corpus is the exact same as the
    original.
    """
    copyLocation = os.path.join(tempfile.mkdtemp(), "test")
    self.corpus.copy(copyLocation)

    copyCorpus = nab.corpus.Corpus(copyLocation)

    for relativePath in list(self.corpus.dataFiles.keys()):
      self.assertIn(relativePath, list(copyCorpus.dataFiles.keys()))

      self.assertTrue(
        all(self.corpus.dataFiles[relativePath].data == \
            copyCorpus.dataFiles[relativePath].data))

    shutil.rmtree(copyLocation)


  def testAddDataSet(self):
    """
    Test the addDataSet() function, specifically check if it adds a new
    data file in the correct location in directory and into the dataFiles
    attribute.
    """
    copyLocation = os.path.join(tempfile.mkdtemp(), "test")
    copyCorpus = self.corpus.copy(copyLocation)

    for relativePath, df in self.corpus.dataFiles.items():
      newPath = relativePath + "_copy"
      copyCorpus.addDataSet(newPath, copy.deepcopy(df))

      self.assertTrue(all(copyCorpus.dataFiles[newPath].data == df.data))

    shutil.rmtree(copyLocation)


  def testGetDataSubset(self):
    """
    Test the getDataSubset() function, specifically check if it returns only
    dataFiles with relativePaths that contain the query given.
    """
    query1 = "realAWSCloudwatch"
    subset1 = self.corpus.getDataSubset(query1)

    self.assertEqual(len(subset1), 2)
    for relativePath in list(subset1.keys()):
      self.assertIn(query1, relativePath)

    query2 = "artificialWithAnomaly"
    subset2 = self.corpus.getDataSubset(query2)

    self.assertEqual(len(subset2), 1)

    for relativePath in list(subset2.keys()):
      self.assertIn(query2, relativePath)


if __name__ == '__main__':
  unittest.main()
