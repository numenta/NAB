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
real-world timeseries containing labeled anomalous periods of behavior.

All data are ordered, timestamped, single valued metrics collected at 5 minute
intervals.

Data represent metric values from common AWS server metrics as collected by
the Amazon Cloudwatch service. Example metrics include CPU Utilization, Network
Bytes In, and Disk Read Bytes.

#### Task

Detect anomalous behavior in streaming data in real-time.

As noted in the paper, the real-world task of streaming anomaly detection is
challenging for several reasons and these place significant constraints on the
allowable methods.

You must be able to provide a reliable anomaly score with minimal prior
knowledge of the data. There is hardly ever a single 'normal' set of statistics
for a streaming dataset and those statistics change constantly.

You must be able to provide a classification in a reasonable amount of time.
This benchmark is representative of a task in human time-scales. Microsecond
responses are not required, but hour-long determinations are unacceptable. Here
it is expected that record classification should take place in far less than 5
minutes.

You must minimize the impact, which is often financial, on the institution
making use of your detection technique. It is insufficient to just catch all
anomalies as a concurrent high false-positive rate can reduce or eliminate an
institution's willingness to use your technique.

Each of these constraints is handled explicitly by the code in this repository.
We hope this will allow you to quickly get a useful, real-world evaluation of
your anomaly detection method.

### Requirements

We provide scripts that will allow you generate results under the same
constraints used in the Numenta paper. To use that code you will need to have
the following installed.

- [Python 2.7](https://www.python.org/download/)
- [Pandas](http://pandas.pydata.org/)
- [Git](http://git-scm.com/book/en/Getting-Started-Installing-Git)

In addition we provide all of the scripts we used to generate our results using
CLA. To replicate those results you will also need to install:

- [NuPIC Source](http://www.github.com/numenta/nupic)

#### Optional Extras

- [Plotly](https://plot.ly/)

If you would like these scripts to plot results you can sign up for a free Plot.ly
account and install their Python library.

After you have signed up you will need to add your username and API key to your
environment.

    export PLOTLY_USER_NAME='{YOUR PLOTLY USERNAME}'
    export PLOTLY_API_KEY='{YOUR API KEY}'

You can then add the --plot option to any python script to visualize output.

### Installation

##### Update NuPIC to the correct commit to replicate the paper's results

    cd /path/to/nupic/
    git checkout -b nab 1ea2bf51b7a5d93673a4c5b80489b8f95d782028

Then follow build directions in /path/to/nupic/README.md

##### Download this repository

    cd ~/
    git clone git@github.com:numenta/nab.git

### Usage


#### Replicate Our Results

    cd /path/to/nab
    ./run_benchmark.sh

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
- Add in threshold and adaptive threshold based measures for comparison