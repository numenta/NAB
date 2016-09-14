The Numenta Anomaly Benchmark [![Build Status](https://travis-ci.org/numenta/NAB.svg?branch=master)](https://travis-ci.org/numenta/NAB)
-----------------------------

Welcome. This repository contains the data and scripts comprising the Numenta
Anomaly Benchmark (NAB). NAB is a novel benchmark for evaluating
algorithms for anomaly detection in streaming, real-time applications. It is
comprised of over 50 labeled real-world and artificial timeseries data files plus a
novel scoring mechanism designed for real-time applications.

Included are the tools to allow you to easily run NAB on your
own anomaly detection algorithms; see the [NAB entry points
info](https://github.com/numenta/NAB/wiki#nab-entry-points). Competitive results
tied to open source code will be posted in the wiki on the
[Scoreboard](https://github.com/numenta/NAB/wiki/NAB%20Scoreboard). Let us know
about your work by emailing us at [nab@numenta.org](mailto:nab@numenta.org) or
submitting a pull request.

This readme is a brief overview and contains details for setting up NAB. Please
refer to the [NAB publication](http://arxiv.org/abs/1510.03336) or the [NAB
Whitepaper](https://github.com/numenta/NAB/wiki#nab-whitepaper) in the wiki for
more details about NAB scoring, data, motivation, etc.

We encourage you to publish your results on running NAB, and share them with us at [nab@numenta.org](nab@numenta.org). Please cite the following publication when referring to NAB:

Lavin, Alexander and Ahmad, Subutai. *"Evaluating Real-time Anomaly Detection
Algorithms – the Numenta Anomaly Benchmark"*, Fourteenth International
Conference on Machine Learning and Applications, December 2015.
[[PDF]](http://arxiv.org/abs/1510.03336)

#### Scoreboard

The NAB scores are normalized such that the maximum possible is 100.0 (i.e. the perfect detector), and a baseline of 0.0 is determined by the "null" detector (which makes no detections).

| Detector      | Standard Profile | Reward Low FP | Reward Low FN |
|---------------|------------------|---------------|---------------|
| Perfect       | 100.0            | 100.0         | 100.0         |
| [CAD OSE](https://github.com/smirmik/CAD)&dagger; | 69.9          | 67.0          | 73.2          |
| [Numenta HTM](https://github.com/numenta/nupic)* | 65.3          | 58.6          | 69.4          |
| [Relative Entropy](http://www.hpl.hp.com/techreports/2011/HPL-2011-8.pdf) | 54.6 | 47.6 | 58.8 |
| [Twitter ADVec v1.0.0](https://github.com/twitter/AnomalyDetection)| 47.1             | 33.6          | 53.5          |
| [Sliding Threshold](https://github.com/numenta/NAB/blob/master/nab/detectors/gaussian/windowedGaussian_detector.py) | 39.6             | 20.9         | 47.4          |
| [Etsy Skyline](https://github.com/etsy/skyline) | 35.7             | 27.1          | 44.5          |
| Bayesian Changepoint**          | 17.7              | 3.2           | 32.2           |
|  [EXPoSE](https://arxiv.org/abs/1601.06602v3)   | 16.4     | 3.2  | 26.9     |
| Random***       | 11.0             | 1.2          | 19.5          |
| Null          | 0.0              | 0.0           | 0.0           |

*As of NAB v1.0*

\* The results correspond to NuPIC and nupic.core SHAs 42f701d and c030b84 respectively, but the latest version of NuPIC should still work (the results may not be identical).

** The original algorithm was not designed for anomaly detection. Details of the implementation and parameter tuning are in the [detector's code](https://github.com/numenta/NAB/blob/master/nab/detectors/bayes_changept/bayes_changept_detector.py).

*** Scores reflect the mean across a range of random seeds. The spread of scores for each profile are 7.95 to 16.83 for Standard, -1.56 to 2.14 for Reward Low FP, and 11.34 to 23.68 for Reward Low FN.

&dagger; Algorithm was an entry to the [2016 NAB Competition](http://numenta.com/blog/2016/08/10/numenta-anomaly-benchmark-nab-competition-2016-winners/).

Please see [the wiki section on contributing algorithms](https://github.com/numenta/NAB/wiki/NAB-Contributions-Criteria#anomaly-detection-algorithms) for discussion on posting algorithms to the scoreboard.

#### Corpus

The NAB corpus of 58 timeseries data files is designed to provide data for research
in streaming anomaly detection. It is comprised of both
real-world and artifical timeseries data containing labeled anomalous periods of behavior.

The majority of the data is real-world from a variety of sources such as AWS
server metrics, Twitter volume, advertisement clicking metrics, traffic data,
and more. All data is included in the repository, with more details in the [data
readme](https://github.com/numenta/NAB/tree/master/data). We are in the process
of adding more data, and actively searching for more data. Please contact us at
[nab@numenta.org](mailto:nab@numenta.org) if you have similar data (ideally with
known anomalies) that you would like to see incorporated into NAB.

The NAB version will be updated whenever new data (and corresponding labels) is
added to the corpus; NAB is currently in v1.0.

#### Additional Scores

For comparison, here are the NAB V1.0 scores for some additional flavors of HTM.

* NumentaTM HTM detector uses the implementation of temporal memory found
[here](https://github.com/numenta/nupic.core/blob/master/src/nupic/algorithms/TemporalMemory.hpp).
* Numenta HTM detector with no likelihood uses the raw anomaly scores directly. To
run without likelihood, set the variable `self.useLikelihood` in
[numenta_detector.py](https://github.com/numenta/NAB/blob/master/nab/detectors/numenta/numenta_detector.py)
to `False`.
* [nab-comportex](https://github.com/floybix/nab-comportex) is a twist on HTM  anomaly detection using [Comportex](https://github.com/htm-community/comportex), a community-driven HTM implementation in Clojure. Please see [Felix Andrew's blog post](http://floybix.github.io/2016/07/01/attempting-nab) on experiments with this algorithm.


| Detector      |Standard Profile | Reward Low FP | Reward Low FN |
|---------------|---------|------------------|---------------|---------------|
| Numenta HTM*   | 65.3             | 58.6       | 69.4          |
| [nab-comportex](https://github.com/floybix/nab-comportex)&dagger; | 64.6             | 58.8       | 69.6          |
| [NumentaTM HTM](https://github.com/numenta/NAB/blob/master/nab/detectors/numenta/numentaTM_detector.py)* | 61.2             | 52.4       | 66.1          |
| Numenta HTM*, no likelihood | 52.52 | 41.09    | 58.25         |

\* The results correspond to NuPIC and nupic.core SHAs 42f701d and c030b84
respectively, but the latest version of NuPIC should still work (the results may
not be identical).

&dagger; Algorithm was an entry to the [2016 NAB Competition](http://numenta.com/blog/2016/08/10/numenta-anomaly-benchmark-nab-competition-2016-winners/).

Installing NAB 1.0
------------------

### Supported Platforms

- OSX 10.9 and higher
- Amazon Linux (via AMI)

Other platforms may work but have not been tested.


### Initial requirements

You need to manually install the following:

- [Python 2.7](https://www.python.org/download/)
- [pip](https://pip.pypa.io/en/latest/installing.html)
- [NumPy](http://www.numpy.org/)
- [NuPIC](http://www.github.com/numenta/nupic) (only required if running the Numenta detector)

##### Download this repository

Use the Github links provided in the right sidebar.

##### Install the Python requirements

    cd NAB
    (sudo) pip install -r requirements.txt

This will install the additional required modules pandas and simplejson.

##### Install NAB

Recommended:

	python setup.py install --user

Or if you are actively working on the code and are familiar with manual
PYTHONPATH setup:

	python setup.py develop --prefix=/some/other/path/

### Usage

There are several different use cases for NAB:

1. If you just want to look at all the results we reported in the paper, there
is no need to run anything. All the data files are in the data subdirectory and
all individual detections for reported algorithms are checked in to the results
subdirectory. Please see the README files in those locations.

1. If you want to plot some of the results, please see the README in the
`scripts` directory for `scripts/plot.py`

1. If you have your own algorithm and want to run the NAB benchmark, please see
the [NAB Entry Points](https://github.com/numenta/NAB/wiki#nab-entry-diagram)
section in the wiki. (The easiest option is often to simply run your algorithm
on the data and output results in the CSV format we specify. Then run the NAB
scoring algorithm to compute the final scores. This is how we scored the Twitter
algorithm, which is written in R.)

1. If you are a NuPIC user and just want to run the Numenta HTM detector follow
the directions below to "Run HTM with NAB".

1. If you want to run everything including the bundled Skyline detector follow
the directions below to "Run full NAB". Note that this will take hours as the
Skyline code is quite slow.

1. If you just want to run NAB on one or more data files (e.g. for debugging)
follow the directions below to "Run a subset of NAB".


##### Run HTM with NAB

First make sure NuPIC is installed and working properly. Then:

    cd /path/to/nab
    python run.py -d numenta --detect --score --normalize

This will run the Numenta detector only and produce normalized scores. Note that
by default it tries to use all the cores on your machine. The above command
should take about 20-30 minutes on a current powerful laptop with 4-8 cores.
For debugging you can run subsets of the data files by modifying and specifying
specific label files (see section below). Please type:

    python run.py --help

to see all the options.

Note that to replicate results exactly as in the paper you may need to checkout
the specific version of NuPIC (and associated nupic.core) that is noted in the
[Scoreboard](https://github.com/numenta/NAB/wiki/NAB%20Scoreboard):

    cd /path/to/nupic/
    git checkout -b nab {TAG NAME}
    cd /path/to/nupic.core/
    git checkout -b nab {TAG NAME}


##### Run full NAB

    cd /path/to/nab
    python run.py

This will run everything and produce results files for all anomaly detection
methods. Several algorithms are included in the repo, such as the Numenta
HTM anomaly detection method, as well as methods from the [Etsy
Skyline](https://github.com/etsy/skyline) anomaly detection library, a sliding
window detector, Bayes Changepoint, and so on. This will also pass those results
files to the scoring script to generate final NAB scores. **Note**: this option
will take many many hours to run.

##### Run subset of NAB data files

For debugging it is sometimes useful to be able to run your algorithm on a
subset of the NAB data files or on your own set of data files. You can do that
by creating a custom `combined_windows.json` file that only contains labels for
the files you want to run. This new file should be in exactly the same format as
`combined_windows.json` except it would only contain windows for the files you
are interested in. 

**Example**: an example file containing two files is in
`labels/combined_windows_tiny.json`.  The following command shows you how to run
NAB on a subset of labels:

    cd /path/to/nab
    python run.py -d numenta --detect --windowsFile labels/combined_windows_tiny.json

This will run the `detect` phase of NAB on the data files specified in the above
JSON file. Note that scoring and normalization are not supported with this
option. Note also that you may see warning messages regarding the lack of labels
for other files. You can ignore these warnings.

