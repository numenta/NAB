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
in streaming anomaly detection. It is comprised of both artificial and real
world timeseries containing anomalous periods of behavior.

### Requirements

To use the code in this repository you must have the following installed on
your system.

- [Python 2.7](https://www.python.org/download/)
- [NuPIC](http://www.github.com/numenta/nupic)

### Installation

    git clone git@github.com:numenta/nab.git

### Usage

    cd /path/to/nab
    python runBenchmark.py



