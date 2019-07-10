################################################################################
# This script runs the Twitter AnomalyDetection algorithms on the NAB data set.
#
# You must first install the AnomalyDetection package:
# https://github.com/twitter/AnomalyDetection#how-to-get-started
#
# You must also have NAB installed and specify the path at the bottom of this
# script.
################################################################################

library(methods)
library(AnomalyDetection)
library(jsonlite)



addDetections <- function(anomalyDataFrame, detections, algorithmName) {
  anomalyDataFrame$anomaly_score=0.0

  if (length(detections$anoms) > 0) {
    for (i in 1:nrow(detections$anoms)) {
      if (algorithmName == "twitterADTs") {
        idx = match(detections$anoms[i, 1], anomalyDataFrame$timestamp)
      }
      else if (algorithmName == "twitterADVec") {
        idx = detections$anoms[i, 1]
      }
      anomalyDataFrame[idx,]$anomaly_score = 1.0
    }
  }
  return(anomalyDataFrame)
}


addLabels <- function(anomalyDataFrame, anomalyBounds) {
  anomalyDataFrame$label = 0

  if (length(anomalyBounds) != 0) {
    for (i in 1:nrow(anomalyBounds)) {
      lower = anomalyBounds[i, 1]
      upper = anomalyBounds[i, 2]
      idx = anomalyDataFrame$timestamp >= lower & anomalyDataFrame$timestamp <= upper
      idx[is.na(idx)] = FALSE
      anomalyDataFrame[idx,]$label = 1
    }
  }
  return(anomalyDataFrame)
}


runTwitter <- function(algorithmName, nab_data, filename) {

  if (algorithmName == "twitterADTs") {
    results = tryCatch(
      {
        message(paste(
          "Attempting detection w/ AnomalyDetectionTS on ", filename))
        AnomalyDetectionTs(
          nab_data, max_anoms=0.0008, direction='both', plot=FALSE)
      },
      error = function(cond) {
        message(paste("Unable to run the algorithm for ", filename))
      return(NULL)
      }
    )
  }
  else if (algorithmName == "twitterADVec") {
    message(paste("Detecting w/ AnomalyDetectionVec on ", filename))
    results = AnomalyDetectionVec(
      nab_data[,2], alpha=0.05, period=150, max_anoms=0.0020, direction='both',
      plot=FALSE)
  }

  message("Results...")
  print(results$anoms)

  return(results)
}


main <- function(pathToNAB, algorithmName, skipFiles=list()) {
  # pathToNAB (character): string specifying path to the NAB dir.
  # algorithmName (character): either 'twitterADTs' or 'twitterADVec'.
  # skipFiles (list): file names to skip; useful in debugging.

  # Format dates: coerce from character class to nabDate class
  setClass("nabDate")
  setAs(
    "character",
    "nabDate",
    function(from) as.POSIXlt(from, format="%Y-%m-%d %H:%M:%OS"))

  # Setup paths to NAB data and results
  nabDataDir = paste(pathToNAB, "data", sep='/')
  dataDirs = list.files(nabDataDir)
  resultsDir = paste(pathToNAB, "results", algorithmName, sep='/')

  # Get the truth anomaly windows
  windows = fromJSON(paste(pathToNAB, "labels/combined_windows.json", sep='/'))

  for (dDir in dataDirs) {
    dataFiles = list.files(paste(nabDataDir, dDir, sep='/'))
    for (dFile in dataFiles) {
      if (is.element(dFile, skipFiles)) {
        next
      }

      # Get the data and run the detector
      dataName = paste(dDir, dFile, sep='/')
      dFilePath = paste(nabDataDir, dataName, sep='/')
      nab_data = read.csv(dFilePath, colClasses=c("nabDate", "numeric"))
      results = runTwitter(algorithmName, nab_data, dFilePath)

      # Populate dataframe with anomaly scores and truth labels
      nab_data = addDetections(nab_data, results, algorithmName)
      nab_data = addLabels(nab_data, windows[[dataName]])

      # Write results to csv
      resultsFileName = paste(algorithmName, dFile, sep='_')
      write.csv(
        nab_data,
        paste(resultsDir, dDir, resultsFileName, sep='/'),
        row.names=FALSE)
    }
  }
}



pathToNAB = "path/to/nab"
skipFiles = list()
algorithmNames = list("twitterADVec", "twitterADTs")
for (alg in algorithmNames) {
  main(pathToNAB, alg)
}
