## Introduction

[AnomalyDetection](https://github.com/twitter/AnomalyDetection) is an R
package developed by Twitter that detects anomalies in time-series data. The
package implements their Seasonal Hybrid ESD algorithm, which extends the
generalized ESD algorithm to allow for seasonality in the data, i.e. different
periods of patterns in the data that represent macro-level changes rather than
micro-level anomalies.

To evaluate AnomalyDetection, written in R, on NAB, written in Python, we have
three options: port the R code into Python, use an interface from R to Python
like rpy2, or use the R code for anomaly detection and the Python code for
evaluating the results. We elected to go with the third option, following
"Path 3" in [this NAB
figure](https://drive.google.com/a/numenta.com/file/d/0B1_XUjaAXeV3NmxhbEFtZVZ4TmM/view?pli=1).
Thus the task reduced to converting the NAB data files into structures as
expected by AnomalyDetection, and then converting the output of
AnomalyDetection into the results format required by NAB.

## Step 1 - run the detection algorithms

We provide a the R script (nab_anomaly_detection.r) we used to run the
AnomlayDetection algorithms on NAB, which includes a few subtleties detailed
below.

### Handling NAB datasets in R

As specified in [the NAB technical
whitepaper](https://github.com/numenta/NAB/wiki#nab-whitepaper),
datasets in NAB are CSV files with a "timestamp" column and a "value" column.
The values are floats or integers, and the timestamps are strings of the form
`YYYY-mm-dd HH:MM:SS.s` (in Python notation). In R notation, the timestamps
are of the form `%Y-%m-%d %H:%M:%OS`. R provides a `read.csv` function to load
NAB data into a dataframe that AnomalyDetection can use. Converting the
timestamps in the CSV file to the appropriate datatype in R requires a bit of
subtlety. With the path to the CSV file stored in `dataFilePath`,

     setClass("nabDate")
     setAs("character", "nabDate", function(from) as.POSIXlt(from, format="%Y-%m-%d %H:%M:%OS"))
     nab_data <- read.csv(dataFilePath, colClasses=c("nabDate", "numeric"))

Now `nab_data` can be passed into the AnomalyDetection functions.

### AnomalyDetectionTs issues

The Ts version of AnomalyDetection is intended to use the periodocity in time
series data to supplement the underlying algorithms. However, we found the
algorithm failed to detect the necessary periodicity params for a large subset
of the NAB data files. Researching the errors revealed open issues in the
AnomalyDetection source code, where the recommended course of action is to
defer to the Vec version. Therefore we do not include the Ts version in the
NAB results.

There are two error statements and corresponding AnomalyDetection issues:
["Anom detection needs at least 2 periods worth of
data"](https://github.com/twitter/AnomalyDetection/issues/15) and ["must
supply period length for time series
decomposition"](https://github.com/twitter/AnomalyDetection/issues/45).

### Tuning the AnomalyDetection parameters

We tuned the parameters of AnomalyDetectionVec to yield the best NAB results
possible (across all application profiles), and the AnomalyDetectionTs
parameters in an attempt to run it effectively on most of the dataset.

The parameters of significant consequence to the results of
AnomalyDetectionVec are `period` and `max_anoms`. The former defines the
number of records in a single period (used in seasonal decomposition), and the
latter captures the maximum percent of data points that will be labelled as
anomalous by the algorithm. We tuned these parameters manually in search of
the best final scores, finding `period=150` and `max_anoms = 0.0020` maximize
the scores for all three NAB application profiles (standard, reward low FP,
reward low FN).

## Step 2 - prepare to run NAB

To prepare NAB for analyzing results from a new detector, we ran the following script:

    python scripts/create_new_detector.py --detector twitterADVec

This script generates the necessary directories and creates an entry in the thresholds JSON.

### Formatting the results for NAB

NAB requires a CSV file with timestamp, value, anomaly_score, and label
columns, so we want to add these columns to our `nab_data` data frame. Because
AnomalyDetection identifies anomalies, rather than reporting an anomaly
probability or a raw score for each record, we used a binary anomaly_score:
the records flagged by AnomalyDetection as anomalous are represented by 1, and
all others 0. The label column is also binary, indicating whether or not a
record is within a true anomaly window. The true anomalies and their durations
are recorded in a [JSON file of the combined
windows](https://github.com/numenta/NAB/blob/master/labels/combined_windows.json).
We  used the
[jsonlite](http://cran.r-project.org/web/packages/jsonlite/index.html) R
package for handling the JSON.

With all columns added to the dataframe, `write.csv` lets us write the results
to a CSV file that can be passed into NAB. **Note:** Each CSV file must have
the name of the detector followed by an underscore at the beginning of the
filename, e.g. `twitterADVec_cpu_utilization_asg_misconfiguration.csv`.

This is implemented in `addDetections()` and `addLabels()` of our script for running AnomalyDetection.

## Step 3 - run NAB

The results CSV files were placed in NAB/results/twitterADVec/ in categorical
subdirectories. Now we're ready to score the results, and in the top level of
NAB we run:

    python run.py -d twitterADVec --optimize (optional) --score --normalize
    
This runs the scoring and normalization step for the twitterADVec detector.
The optimization step is optional because we can manually set the thresholds
(for all application profiles) arbitrarily between 0 and 1. That is, because
the anomaly_score entries are binary, we can use a threshold of 0.5 and skip
optimization.

The final scores will be printed to the screen and written to
[nab/results/final_results.json](https://github.com/numenta/NAB/blob/master/results/final_results.json),
and results CSV files for each application profile will be written to the
twitterADVec directory. We obtained the following output for
AnomalyDetectionVec with optimized parameters:

    Final score for 'twitterADVec_reward_low_FP_rate_scores' = 33.61
    Final score for 'twitterADVec_reward_low_FN_rate_scores' = 53.50
    Final score for 'twitterADVec_standard_scores' = 47.06
