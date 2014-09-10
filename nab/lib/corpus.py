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
"""
This contains the objects to store and manipulate a database of csv files.
"""

import os
import sys
import copy
import pandas
from nab.lib.util import absoluteFilePaths, createPath



class DataSet(object):
  """
  Class for storing and manipulating a dataset within a corpus
  Data is stored in pandas.DataFrame
  """

  def __init__(self, srcPath):
    """
    @param srcPath (string)   Path to read dataset from, data should be in csv
                              fomat.
    """
    self.srcPath = srcPath

    self.fileName = os.path.split(srcPath)[1]

    self.data = pandas.io.parsers.read_csv(self.srcPath,
                                          header=0, parse_dates=[0])


  def write(self, newPath=None):
    """
    Write dataset to self.srcPath or newPath if given

    @param newPath (string)   Path to write dataset to. If path is not given,
                              write to source path
    """

    path = newPath if newPath else self.srcPath
    print 'write to:', path
    self.data.to_csv(path, index=False)


  def modifyData(self, columnName, data=None, write=False):
    """
    Modify dataset
    Add columnName to dataset if data is given
    otherwise, remove columnName from dataset

    @param columnName (string)          Name of the column in the dataset to
                                        either add or remove.

    @param data       (pandas.Series)   Column data to be added to dataset.
                                        Data length should be as long as the
                                        length of other columns.

    @param write      (boolean) Flag to choose whether to write modifications to
                                source path.
    """
    print columnName, type(data), write

    if isinstance(data, pandas.Series):
      self.data[columnName] = data
    else:
      if columnName in self.data:
        del self.data[columnName]

    if write:
      self.write()


  def getTimestampRange(self, t1, t2):
    """
    Given timestamp range, get all records that are within that range.

    @param t1   (int)   Starting timestamp.

    @param t2   (int)   Ending timestamp.

    @return     (list)  Timestamp and value for each time stamp within the
                        timestamp range.
    """
    tmp = self.data[self.data["timestamp"] >= t1]
    ans = tmp[tmp["timestamp"] <= t2]["timestamp"].tolist()
    return ans


  def __str__(self):
    ans = ""
    ans += "path:                %s\n" % self.srcPath
    ans += "file name:           %s\n"% self.fileName
    ans += "data size:         ", self.data.shape()
    ans += "sample line: %s\n" % ", ".join(self.data[0])
    return ans


class Corpus(object):
  """
  Class for storing and manipulating a corpus of data where each dataset is
  stored as a DataSet object.
  """

  def __init__(self, srcRoot):
    """
    @param srcRoot    (string)    Source directory of corpus.
    """
    self.srcRoot = srcRoot
    self.dataSets = self.getDataSets()
    self.numDataSets = len(self.dataSets)


  def getDataSets(self):
    """
    Collect dataSets from self.srcRoot where datasets are stored in a dictionary
    in which the path relative to the self.srcRoot is their key.

    @return (dict)    Dictionary containing key value pairs of a relative path
                      and its corresponding dataset.
    """
    filePaths = absoluteFilePaths(self.srcRoot)
    dataSets = [DataSet(path) for path in filePaths]

    def getRelativePath(srcRoot, srcPath):
      return srcPath[srcPath.index(srcRoot)+len(srcRoot):].strip("/")

    dataSets = {getRelativePath(self.srcRoot, d.srcPath) : d \
                                                            for d in dataSets}
    return dataSets


  def addColumn(self, columnName, data, write=False):
    """
    Add column to entire corpus given columnName and dictionary of data for each
    file in the corpus. If newRoot is given then corpus is copied and then
    modified.

    @param columnName   (string)  Name of the column in the dataset to add.

    @param data         (dict)    Dictionary containing key value pairs of a
                                  relative path and its corresponding
                                  dataset (as a pandas.Series).

    @param write        (boolean) Flag to decide whether to write corpus
                                  modificiations or not.
    """

    for relativePath in self.dataSets.keys():
      self.dataSets[relativePath].modifyData(columnName, data[relativePath], write=write)


  def removeColumn(self, columnName, write=False):
    """
    Remove column from entire corpus given columnName. If newRoot if given then
    corpus is copied and then modified.

    @param columnName   (string)  Name of the column in the dataset to add.

    @param write        (boolean) Flag to decide whether to write corpus
                                  modificiations or not.
    """
    for relativePath in self.dataSets.keys():
      self.dataSets[relativePath].modifyData(columnName, write=write)

    return corp


  def copy(self, newRoot=None):
    """
    Copy corpus to a newRoot which cannot already exist

    @param newRoot      (string)      Location of new directory to copy corpus
                                      to.
    """
    print 'got to copy()'
    if newRoot[-1] != "/":
      newRoot += "/"
    if os.path.isdir(newRoot):
      print "directory already exists"
      return
    else:
      createPath(newRoot)

    print newRoot
    newCorpus = Corpus(newRoot)
    print self.dataSets.keys()
    for relativePath in self.dataSets.keys():
      newCorpus.addDataSet(relativePath, self.dataSets[relativePath])
      print "adding %s" % os.path.join(newRoot, relativePath)
    return newCorpus


  def addDataSet(self, relativePath, dataSet):
    """
    Add dataset to corpus given its realtivePath within the corpus

    @param relativePath     (string)      Path of the new dataset relative to
                                          the corpus directory.

    @param dataSet          (dataSet)     Data set to be added to corpus.
    """
    print 'addDataSet'
    self.dataSets[relativePath] = copy.deepcopy(dataSet)
    newPath = self.srcRoot + relativePath
    createPath(newPath)
    self.dataSets[relativePath].srcPath = newPath
    print 'write'
    self.dataSets[relativePath].write()
    self.numDataSets = len(self.dataSets)


  def getDataSubset(self, query):
    """
    Get subset of the corpus given a query to match the dataset filename or
    relative path.

    @param query        (string)      Search query for obtainin the subset of
                                      the corpus.

    @return             (dict)        Dictionary containing key value pairs of a
                                      relative path and its corresponding
                                      dataset.
    """
    ans = {}
    for relativePath in self.dataSets.keys():
      if query in relativePath:
        ans[relativePath] = self.dataSets[relativePath]
    return ans
