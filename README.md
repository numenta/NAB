
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
[Scoreboard](https://github.com/numenta/NAB/wiki#nab-scoreboard). Let us know
about your work by submitting a pull request.

This readme is a brief overview and contains details for setting up NAB.
Please refer to the NAB publication (forthcoming) or the [NAB
Whitepaper](https://github.com/numenta/NAB/wiki#nab-whitepaper) in the wiki for
more details about NAB scoring, data, motivation, etc.

Please cite the following publication when referring to NAB (link and PDF
forthcoming):

Lavin, Alex and Ahmad, Subutai. *"Evaluating Real-time Anomaly Detection
Algorithms – the Numenta Anomaly Benchmark"*, Fourteenth International Conference
on Machine Learning and Applications, December 2015.

#### Corpus

The NAB corpus of timeseries data files is designed to provide data for research
in streaming anomaly detection. It is comprised of both
real-world and artifical timeseries data containing labeled anomalous periods of behavior.

The majority of the data is real-world from a variety of sources such as AWS
server metrics, Twitter volume, advertisement clicking metrics, traffic data,
and more. All data is included in the repository, with more details in the [data
readme](https://github.com/numenta/NAB/tree/master/data). We are in the process
of adding more data, and actively searching for more data. Please contact us at
nab@numenta.org if you have similar data (ideally with known anomalies) that you
would like to see incorporated into NAB.

The NAB version will be updated whenever new data (and corresponding labels) is
added to the corpus; NAB is currently in v0.8.

#### Task

Detect anomalous behavior in *streaming data in real-time* and provide *useful* alerts.

Your anomaly detector must be able to handle streaming data. Post-hoc analysis is insufficient for this task. All classifications must
be done as if the data is being presented for the first time, in real time. Anomalies must be detected within a reasonable amount of time.

This benchmark is representative of a task in human time-scales. Per-record classification should take place in less than 5 minutes. Anomaly detection should happen as quickly as possible following the onset of an anomaly.

It is insufficient to just catch all anomalies. A detector with a high false positive rate is of little use. I.e. many false positives will reduce or eliminate an institution's willingness to use your technique; you must minimize the cost of using your detection technique.

Installing NAB 0.8
--------------

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

    cd ~/
    git clone https://github.com/numenta/NAB.git

##### Install the Python requirements

    cd NAB
    (sudo) pip install -r requirements.txt

This will install the additional required modules pandas and simplejson.

##### Install NAB

	(sudo) python setup.py develop

Or with manual PYTHONPATH setup, rather than sudo:

	python setup.py develop --prefix=/some/other/path/

### Usage

##### Run NAB

    cd /path/to/nab
    python run.py

This will produce results files for the anomaly detection methods. Included in the repo are the Numenta anomaly detection method, as well as methods from the [Etsy Skyline](https://github.com/etsy/skyline) anomaly detection library, a random detector, and a baseline detector. This will also pass those results files to the scoring script to generate final NAB scores.

For details on how to run your own detector please see the [NAB Entry Points diagram](https://github.com/numenta/NAB/wiki#nab-entry-diagram) in the wiki.

To view a description of the command line options please enter

	python run.py --help 

Once NAB is finalized (not yet!) to replicate results exactly you will need a specific version of NuPIC:
    
    cd /path/to/nupic/
    git checkout -b nab {TAG NAME}

Then follow build directions in the [NuPIC "README.md"](https://github.com/numenta/nupic/blob/master/README.md).

#### Data

##### Data and results files

This repo contains a corpus of 32 data files of time-series data. The format of the CSV files is specified in Appendix F of the [NAB Whitepaper](https://github.com/numenta/NAB/wiki#nab-whitepaper). The detector under test will read in, and be scored on, all data files in the corpus. The format of results files is also specified in the whitepaper posted in the wiki.

##### Data and results visualization

There is currently a simple data visualizer available, useful in hand labeling datasets. To use it do the following:

First generate the list of data files and result files:

    ls -1 */*/*.csv | grep data > data_file_paths.txt 
    ls -1 */*/*/*.csv | grep results | grep -v test_results > results_file_paths.txt

From the NAB directory, type:

    python -m SimpleHTTPServer 12345
 
Then, open Chrome and type this into the url window:
 
    localhost:12345/nab_visualizer.html
 
To view data, click on "look at data", click in query window and press RETURN key. This should show all the data files. You can also filter the files by keyword with the query window; it will filter for filenames that contain the entered characters.

To get a string of the timestamp at a data point, simply click on the data point.

To zoom in on a region of data, drag the cursor to highlight the section of interest. To zoom back out, double-click the screen.

To view result files, click on "look at results" first.

There is a plotting script available in the scripts directory, which will generate plots via the [plotly API](https://plot.ly/); requires a (free) API key. To generate examples, run from the NAB directory:

	python scripts/plot.py

Modify the script to plot specific NAB data and/or results files.