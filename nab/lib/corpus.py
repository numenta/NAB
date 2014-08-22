import os
import copy
import pandas
from nab.lib.util import absoluteFilePaths, createPath

class DataSet(object):
  """
  Class for storing and manipulating a dataset within a corpus
  Data is stored in pandas.DataFrame
  """


  def __init__(self, srcPath):
    self.srcPath = srcPath

    self.fileName = os.path.split(srcPath)[1]

    self.data = pandas.io.parsers.read_csv(self.srcPath,
                                          header=0, parse_dates=[0])


  def write(self, newPath=None):
    """
    Write dataset to self.srcPath or newPath if given
    """
    path = newPath if newPath else self.srcPath
    self.data.to_csv(path, index=False)


  def modifyData(self, columnName, data=None, write=False):
    """
    Modify dataset
    Add columnName to dataset if data is given
    otherwise, remove columnName from dataset
    """
    if data:
      self.data[columnName] = data
    else:
      if columnName in self.data:
        del self.data[columnName]

    if write:
      self.write()


  def getTimestampRange(self, t1, t2):
    """
    Given timestamp range, get all records that are within that range.
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
    self.srcRoot = srcRoot
    self.dataSets = self.getDataSets()
    self.numDataSets = len(self.dataSets)


  def getDataSets(self):
    """
    Collect dataSets from self.srcRoot where datasets are stored in a dictionary
    in which the path relative to the self.srcRoot is their key.
    """
    filePaths = absoluteFilePaths(self.srcRoot)
    dataSets = [DataSet(path) for path in filePaths]

    def getRelativePath(srcRoot, srcPath):
      return srcPath[srcPath.index(srcRoot)+len(srcRoot):].strip("/")

    dataSets = {getRelativePath(self.srcRoot, d.srcPath) : d \
                                                            for d in dataSets}
    return dataSets


  def addColumn(self, columnName, data, write=False, newRoot=None):
    """
    Add column to entire corpus given columnName and dictionary of data for each
    file in the corpus. If newRoot is given then corpus is copied and then
    modified.
    """
    corp = self.copy(newRoot) if newRoot else self
    for relativePath in self.dataSets.keys():
      corp.dataSets[relativePath].modifyData(columnName, data[relativePath], write=write)

    return corp


  def removeColumn(self, columnName, write=False, newRoot=None):
    """
    Remove column from entire corpus given columnName. If newRoot if given then
    corpus is copied and then modified.
    """
    corp = self.copy(newRoot) if newRoot else self
    for relativePath in self.dataSets.keys():
      corp.dataSets[relativePath].modifyData(columnName, write=write)

    return corp


  def copy(self, newRoot=None):
    """
    Copy corpus to a newRoot which cannot already exist
    """

    if newRoot[-1] != "/":
      newRoot += "/"
    if os.path.isdir(newRoot):
      print "directory already exists"
      return
    else:
      createPath(newRoot)
    newCorpus = Corpus(newRoot)
    for relativePath in self.dataSets.keys():
      newCorpus.addDataSet(relativePath, self.dataSets[relativePath])
      print "adding %s" % os.path.join(newRoot, relativePath)
    return newCorpus


  def addDataSet(self, relativePath, dataSet):
    """
    Add dataset to corpus given its realtivePath within the corpus
    """
    self.dataSets[relativePath] = copy.deepcopy(dataSet)
    newPath = self.srcRoot + relativePath
    createPath(newPath)
    self.dataSets[relativePath].srcPath = newPath
    self.dataSets[relativePath].write()
    self.numDataSets = len(self.dataSets)


  def getDataSubset(self, query):
    """
    Get subset of the corpus given a query to match the dataset filename or
    relative path.
    """
    ans = {}
    for relativePath in self.dataSets.keys():
      if query in relativePath:
        ans[relativePath] = self.dataSets[relativePath]
    return ans