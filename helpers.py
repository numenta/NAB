import os
import sys

def getDataGroupDirs(resultPath, detectors):
  # Find sub directories of our results dir, e.g. results/grok/...
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
                "python analyze_results.py -d results/grok")
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