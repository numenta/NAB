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
import copy
import shutil
import pandas
import tempfile
import numpy as np
import unittest2 as unittest

import nab.corpus
from nab.util import recur



class CorpusTest(unittest.TestCase):


  @classmethod
  def setUpClass(cls):
    depth = 3

    cls.root = recur(os.path.dirname, os.path.realpath(__file__), depth)
    cls.corpusSource = os.path.join(cls.root, "tests/test_data")


  def setUp(self):
    self.corpus = nab.corpus.Corpus(self.corpusSource)


  def test_getDataFiles(self):
    """
    Test the getDataFiles() function, specifically check if corpus.dataFiles
    is a dictionary containing DataFile objects containing pandas.DataFrame
    objects to represent the underlying data.
    """
    for df in self.corpus.dataFiles.values():
      self.assertIsInstance(df, nab.corpus.DataFile)
      self.assertIsInstance(df.data, pandas.DataFrame)
      self.assertEqual(set(df.data.columns.values),
        set(["timestamp", "value"]))


  def test_addColumn(self):
    """
    Test the addColumn() function, specificially check if a new column named
    "test" is added.
    """
    columnData = {}
    for relativePath, df in self.corpus.dataFiles.iteritems():
      rows, _ = df.data.shape
      columnData[relativePath] = pandas.Series(np.zeros(rows))

    self.corpus.addColumn("test", columnData, write=False)

    for df in self.corpus.dataFiles.values():
      self.assertEqual(set(df.data.columns.values),
        set(["timestamp", "value", "test"]))


  def test_removeColumn(self):
    """
    Test the removeColumn() function, specifically check if an added column
    named "test" is removed.
    """
    columnData = {}
    for relativePath, df in self.corpus.dataFiles.iteritems():
      rows, _ = df.data.shape
      columnData[relativePath] = pandas.Series(np.zeros(rows))

    self.corpus.addColumn("test", columnData, write=False)

    self.corpus.removeColumn("test", write=False)

    for df in self.corpus.dataFiles.values():
      self.assertEqual(set(df.data.columns.values),
        set(["timestamp", "value"]))


  def test_copy(self):
    """
    Test the copy() function, specifically check if it copies the whole corpus
    to another directory and that the copied corpus is the exact same as the
    original.
    """
    copyLocation = tempfile.mkdtemp()
    shutil.rmtree(copyLocation)
    self.corpus.copy(copyLocation)

    copyCorpus = nab.corpus.Corpus(copyLocation)

    for relativePath in self.corpus.dataFiles.keys():
      self.assertIn(relativePath, copyCorpus.dataFiles.keys())

      self.assertTrue(
        all(self.corpus.dataFiles[relativePath].data == \
            copyCorpus.dataFiles[relativePath].data))

    shutil.rmtree(copyLocation)


  def test_addDataSet(self):
    """
    Test the addDataSet() function, specifically check if it adds a new
    data file in the correct location in directory and into the dataFiles
    attribute.
    """
    copyLocation = tempfile.mkdtemp()
    shutil.rmtree(copyLocation)

    copyCorpus = self.corpus.copy(copyLocation)

    for relativePath, df in self.corpus.dataFiles.iteritems():
      newPath = relativePath + "_copy"
      copyCorpus.addDataSet(newPath, copy.deepcopy(df))

      self.assertTrue(all(copyCorpus.dataFiles[newPath].data == df.data))

    shutil.rmtree(copyLocation)


  def test_getDataSubset(self):
    """
    Test the getDataSubset() function, specifically check if it returns only
    dataFiles with relativePaths that contain the query given.
    """
    query1 = "realAWSCloudwatch"
    subset1 = self.corpus.getDataSubset(query1)

    self.assertEqual(len(subset1), 2)
    for relativePath in subset1.keys():
      self.assertIn(query1, relativePath)

    query2 = "artificialWithAnomaly"
    subset2 = self.corpus.getDataSubset(query2)

    self.assertEqual(len(subset2), 1)

    for relativePath in subset2.keys():
      self.assertIn(query2, relativePath)



if __name__ == '__main__':
  unittest.main()
