import os
import sys
import yaml
import pandas

from collections import OrderedDict

from confusion_matrix import (WindowedConfusionMatrix,
                              pPrintMatrix)

def sharedSetup(options):   
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

  # Find sub directories of our results dir, e.g. results/numenta/...
  dataGroupDirs = getDataGroupDirs(options.resultsDir, options.detectors)

  # Infer which detector generated these results from the path
  detector = inferDetector(options.resultsDir, options.detectors)

  return config, profiles, dataGroupDirs, detector

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

def getDetailedResults(csvType, csvFiles, profiles, threshold = None):
  """
  Returns a list of lists suitable for writing to a csv or additional processes.

  csvType - String
  csvFiles - A list of paths to csv files to process
  profiles - A dict mapping profile names to user profiles
  threshold - A value cutoff to apply if working with 'raw' data.
  """

  # Make sure inputs are valid
  if csvType == 'alerts':
    headers = ["Alert Log File"]
    predictedHeader = 'alert'
  elif csvType == 'raw':
    headers = ["Results File"]
    predictedHeader = 'anomaly_score'
  else:
    raise Exception("Unknown csvType.")

  # Analyze all files
  detailedResults = []
  additionalHeaders = ["User Scenario",
                       "True Positives",
                       "False Positives",
                       "False Negatives",
                       "True Negatives",
                       "Cost",
                       "Total Normal",
                       "Possible True Positives"]
  headers.extend(additionalHeaders)

  detailedResults.append(headers)

  # Loop over all specified results files
  for resultsFile in csvFiles:

    with open(resultsFile, 'r') as fh:
      results = pandas.read_csv(fh)
    
    # Loop over user profiles
    for profileName, profile in profiles.iteritems():
      costMatrix = profile['CostMatrix']
      cMatrix = genConfusionMatrix(results,
                                   predictedHeader,
                                   'label',
                                   profile['ScoringWindow'],
                                   5,
                                   costMatrix,
                                   threshold,
                                   verbosity = 0)

      detailedResults.append([resultsFile,
                              profileName,
                              cMatrix.tp, 
                              cMatrix.fp,
                              cMatrix.fn,
                              cMatrix.tn,
                              cMatrix.cost,
                              cMatrix.tn + cMatrix.fp,
                              cMatrix.tp + cMatrix.fn])

  return detailedResults

def genConfusionMatrix(results,
                       predictedHeader,
                       labelHeader,
                       window,
                       windowStepSize,
                       costMatrix,
                       threshold = None,
                       verbosity = 0):
  """
  Returns a confusion matrix object for the results of the
  given experiment and the ground truth labels.
  
    experiment      - an experiment info dict
    threshold       - float - cutoff to be applied to Likelihood scores
    window          - Use a WindowedConfusionMatrix and calculate stats over
                      this many minutes.
    windowStepSize  - The ratio of minutes to records
  """
  
  columnNames = results.columns.tolist()
  if labelHeader not in columnNames:
    print columnNames
    raise Exception('No labels found. Expected a '
                    'column named "%s"' % labelHeader)
  
  if threshold != None:
    # If predicted val is equal or above threshold, label it an anomaly
    predicted = results[predictedHeader].apply(lambda x: 1 if x >= threshold else 0)
  else:
    predicted = results[predictedHeader]

  actual = results[labelHeader]

  if windowStepSize < 1:
    raise Exception("windowStepSize must be at least 1")
  
  cMatrix = WindowedConfusionMatrix(predicted,
                                    actual,
                                    window,
                                    windowStepSize,
                                    costMatrix)

  if verbosity > 0:
    pPrintMatrix(cMatrix, threshold)
  
  return cMatrix

def getDataGroupDirs(resultPath, detectors):
  # Find sub directories of our results dir, e.g. results/numenta/...
  items = os.listdir(resultPath)

  dataGroupDirs = []
  for item in items:
    path = os.path.join(resultPath, item)
    if os.path.isdir(path):
      for d in detectors:
        if d == item: 
          print("ERROR: It looks like you're trying to analyze results from "
                "multiple detectors at once. \nThis script generates results "
                "summaries which are only meaningful on a per-detector basis.\n"
                "Please specify a single detector results directory. e.g. "
                "python analyze_results.py -d results/numenta")
          sys.exit(1)
      dataGroupDirs.append(path)

  return dataGroupDirs

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