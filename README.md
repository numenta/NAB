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
| [Numenta HTM](https://github.com/numenta/nupic)* | 65.3          | 58.6          | 69.4          |
| [Twitter ADVec v1.0.0](https://github.com/twitter/AnomalyDetection)| 47.1             | 33.6          | 53.5          |
| [Etsy Skyline](https://github.com/etsy/skyline) | 35.7             | 27.1          | 44.5          |
| Bayesian Changepoint**          | 17.7              | 3.2           | 32.2           |
| [Sliding Threshold](https://github.com/numenta/NAB/blob/master/nab/detectors/gaussian/windowedGaussian_detector.py) | 15.0             | -26.2          | 30.1          |
| Random***       | 11.0             | 1.2          | 19.5          |
| Null          | 0.0              | 0.0           | 0.0           |

*As of NAB v1.0*

\* The results correspond to NuPIC and nupic.core SHAs 42f701d and c030b84 respectively, but the latest version of NuPIC should still work (the results may not be identical).

** The original algorithm was not designed for anomaly detection. Details of the implementation and parameter tuning are in the [detector's code](https://github.com/numenta/NAB/blob/master/nab/detectors/bayes_changept/bayes_changept_detector.py).

*** Scores reflect the mean across a range of random seeds. The spread of scores for each profile are 7.95 to 16.83 for Standard, -1.56 to 2.14 for Reward Low FP, and 11.34 to 23.68 for Reward Low FN.

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
NumentaTM HTM detector uses the implementation of temporal memory found
[here](https://github.com/numenta/nupic.core/blob/master/src/nupic/algorithms/TemporalMemory.hpp).
Numenta HTM detector with no likelihood uses the raw anomaly scores directly. To
run without likelihood, set the variable `self.useLikelihood` in
[numenta_detector.py](https://github.com/numenta/NAB/blob/master/nab/detectors/numenta/numenta_detector.py)
to `False`.


| Detector      |Standard Profile | Reward Low FP | Reward Low FN |
|---------------|---------|------------------|---------------|---------------|
| Numenta HTM*   | 65.3             | 58.6       | 69.4          |
| [NumentaTM HTM](https://github.com/numenta/NAB/blob/master/nab/detectors/numenta/numentaTM_detector.py)* | 61.2             | 52.4       | 66.1          |
| Numenta HTM*, no likelihood | 52.52 | 41.09    | 58.25         |

\* The results correspond to NuPIC and nupic.core SHAs 42f701d and c030b84
respectively, but the latest version of NuPIC should still work (the results may
not be identical).

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

1. If you just want to look at all
the results we reported in the paper, there is no need to run anything.
All the data files are in the data subdirectory and all individual detections
for reported algorithms are checked in to the results subdirectory. Please see
the README files in those locations.

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


##### Run HTM with NAB

First make sure NuPIC is installed and working properly. Then:

    cd /path/to/nab
    python run.py -d numenta --detect --score --normalize

This will run the Numenta detector only and produce normalized scores. Note that
by default it tries to use all the cores on your machine. The above command
should take about 20-30 minutes on a current powerful laptop with 4-8 cores.
For debugging you can run subsets of the data files by modifying and specifying
specific label files. Please type:

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

This will run everything and produce results files for the anomaly detection
methods. Included in the repo are the Numenta anomaly detection method, as well
as methods from the [Etsy Skyline](https://github.com/etsy/skyline) anomaly
detection library, a random detector, and a null detector. This will also pass
those results files to the scoring script to generate final NAB scores.
**Note**: this option will take many many hours to run.

The run.py command has a number of useful options. To view a description of the
command line options please enter

	python run.py --help 


