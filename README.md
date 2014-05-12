The Numenta Anomaly Benchmark
-----------------------------

### Introduction

This is the companion repository for the upcoming anomaly detection benchmark
paper written by Numenta. It contains all of the relevant data and data
processing scripts so that you can replicate the results in the paper.

We hope you will compare these results with your own anomaly detection methods
and share those results so we can link to them here.

Finally we hope you will help improve these results by contributing to the
Numenta Platform for Intelligent Computing (NuPIC).

### Corpus

The NAB corpus of timeseries datasets is designed to provide data for research
in streaming anomaly detection. It is comprised of both artificial and
real-world timeseries containing anomalous periods of behavior.

### Requirements

To use the code in this repository you must have the following installed on
your system.

- [Python 2.7](https://www.python.org/download/)
- [Pandas](http://pandas.pydata.org/)
- [Git](http://git-scm.com/book/en/Getting-Started-Installing-Git)
- [NuPIC Source](http://www.github.com/numenta/nupic)

### Installation

##### Update NuPIC to the correct commit to replicate the paper's results

    cd /path/to/nupic/
    git checkout -b nab 1ea2bf51b7a5d93673a4c5b80489b8f95d782028

Then follow build directions in /path/to/nupic/README.md

##### Download this repository

    git clone git@github.com:numenta/nab.git

### Usage


#### Replicate Our Results

    cd /path/to/nab
    python runBenchmark.py

This will PRINT OUT / PRODUCE CHART results which should match
exactly to the values in the paper.

#### Analyze Your Results

If you have used the NAB corpus with your own anomaly detection method you can
directly compare your results to ours with the provided script.

    cd /path/to/nab
    python analyze_results.py -i /path/to/your/results.csv

Your results file should be a comma separated file with at least two
columns

    anomaly_score,  label

Anomaly scores must be a floating point values between 0.0 and 1.0.

Labels must be an integer, 0 or 1, that indicates if the record is anomalous
or not.

## TODO

- Update commit sha with final
- Decide what the output of runBenchmark.py should be
  - This will be a results.csv file which will then be passed to analyze_results.py
- Expand detailed description of corpus
- Separate script to take in results and threshold
  - Others will want to use our code for results calc, but theirs for anomaly_score generation
- Try both brute force and log based sampling for ROC curves