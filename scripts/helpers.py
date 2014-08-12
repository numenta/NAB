import os
import sys
import yaml
import pandas

from lib.scoring import Scorer

from collections import OrderedDict

# from confusion_matrix import (WindowedConfusionMatrix,
#                               pPrintMatrix)

def parseConfigFile(options):
  """
  Returns several values used by both
  analyze_results.py and optimize_threshold.py
  """

  # Load the config file
  with open(options.config) as configHandle:
    config = yaml.load(configHandle)

  # Load the profile descriptions
  with open(options.profiles) as profilesHandle:
    profiles = yaml.load(profilesHandle)
    sorted_profiles = sorted(profiles.iteritems())
    profiles = OrderedDict(sorted_profiles)

  # Update any missing config values from global config file
  if not options.resultsDir:
    options.resultsDir = config["ResultsDirectory"]

  options.detectors = config["AnomalyDetectors"]


  # Infer which detector generated these results from the path
  detector = inferDetector(options.resultsDir, options.detectors)

  return profiles, detector

def getCSVFiles(dataGroupDirs, csvType):
  """
  Returns a list of csv files

  dataGroupDirs - List of dir paths within a data dataGroup
  csvType - String - either 'alerts' or 'raw'
  """
  csvFiles = []
  for dataGroupDir in dataGroupDirs:
    rDir = os.path.join(dataGroupDir, csvType)
    items = os.listdir(rDir)
    files = [os.path.join(rDir, item) for
                item in items if item[-4:] == '.csv']
    csvFiles.extend(files)

  if not csvFiles:
    print("No files to analyze.")
    sys.exit(0)

  return csvFiles

def getDetailedResults(resultsCorpus, corpusLabel, profiles, threshold = None):
  """
  Returns a list of lists suitable for writing to a csv or additional processes.

  """
  def convertResultsPathToDataPath(path):
    path = path.split('/')
    detector = path[0]
    path = path[1:]
    path.remove('alerts')

    filename = path[-1]
    toRemove = detector + '_alerts_'
    i = filename.index(toRemove)
    filename = filename[:i] + filename[i+len(toRemove):]

    path[-1] = filename
    path = '/'.join(path)
    return path

  # Analyze all files
  detailedResults = []
  headers = ["File"
             "User Scenario",
             "True Positives",
             "False Positives",
             "False Negatives",
             "True Negatives",
             "Cost",
             "Total Normal",
             "Possible True Positives"]

  detailedResults.append(headers)

  dataSets = resultsCorpus.getDataSubset('/alerts/')

  print dataSets

  # Loop over all specified results files

  for relativePath in dataSets.keys():

    predicted = dataSets[relativePath].data['alert']

    relativePath = convertResultsPathToDataPath(relativePath)
    windows = corpusLabel.windows[relativePath]
    labels = corpusLabel.labels[relativePath]

    # Loop over user profiles
    for profileName, profile in profiles.iteritems():
      costMatrix = profile['CostMatrix']

      score = Scorer(predicted=predicted, labels=labels, windowLimits=windows, costMatrix=costMatrix)

      costMatrix = score.costMatrix

      detailedResults.append([relativePath,
                              profileName,
                              score.score])

  return detailedResults

def inferDetector(path, detectors):
  """
  Returns a string which is either a known detector name or "Unknown" if
  the infered detector does not match one we know.
  """

  guess = os.path.split(path)[1]

  if guess in detectors:
    return guess
  else:
    return "Unknown"