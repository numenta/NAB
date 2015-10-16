
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

| Detector      | Version | Standard Profile | Reward Low FP | Reward Low FN |
|---------------|---------|------------------|---------------|---------------|
| Perfect       | N/A     | 100.0            | 100.0         | 100.0         |
| [Numenta HTM](https://github.com/numenta/nupic)   | current* | 64.7             | 56.5          | 69.3          |
| [Twitter ADVec](https://github.com/twitter/AnomalyDetection) | v1.0.0    | 47.1             | 33.6          | 53.5          |
| [Etsy Skyline](https://github.com/etsy/skyline)  | ???     | 35.7             | 27.1          | 44.5          |
| Random        | N/A     | 16.8             | 5.8          | 25.9          |
| Null          | N/A     | 0.0              | 0.0           | 0.0           |

*As of NAB v1.0*

\* The results correspond to NuPIC and nupic.core SHAs 1777c2d and 9b65900 respectively, but the latest version of NuPIC should still work (the results may not be identical).

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


