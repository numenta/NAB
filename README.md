### Under Construction

#### This repo is under active revision. The code does not work yet. Browse, please don't judge. :)

The Numenta Anomaly Benchmark
-----------------------------

Welcome. This repository contains the data and scripts necessary to replicate the results in the forthcoming Numenta Anomaly Benchmark (NAB) paper. Also provided are the tools to run NAB scoring on your own anomaly detection algorithms. Competitive results tied to open source code will be posted in the wiki on the [Scoreboard](https://github.com/numenta/NAB/wiki#nab-scoreboard). Let us know about your work by submitting a pull request. 

This readme is a brief overview and contains details for setting up NAB. **Please refer to the [NAB Whitepaper](https://github.com/numenta/NAB/wiki#nab-whitepaper) in the wiki for more details about NAB scoring, data, motivation, etc.**

#### Corpus

The NAB corpus of timeseries data files is designed to provide data for research
in streaming anomaly detection. It is comprised of both artificial and
real-world timeseries data containing labeled anomalous periods of behavior.

All data are ordered, timestamped, single-valued metrics collected at 5-minute intervals.

Much of the real-world data are values from AWS server metrics as collected by 
the [AmazonCloudwatch service](https://aws.amazon
.com/documentation/cloudwatch/). Example
metrics include CPU Utilization, Network Bytes In, and Disk Read Bytes. There
are also real world sensor readings from some large machines. 

All data is included in the repository. We are in the process of adding more data, and actively searching for more data.

#### Task

Detect anomalous behavior in *streaming data in real-time* and provide *useful* alerts.

Your anomaly detector must be able to handle streaming data. Post-hoc analysis is insufficient for this task. All classifications must
be done as if the data is being presented for the first time, in real time. Anomalies must be detected within a reasonable amount of time.

This benchmark is representative of a task in human time-scales. Per-record classification should take place in less than 5 minutes. Anomaly detection should happen as quickly as possible following the onset of an anomaly.

It is insufficient to just catch all anomalies. A detector with a high false positive rate is of little use. I.e. many false positives will reduce or eliminate an institution's willingness to use your technique; you must minimize the cost of using your detection technique.

Installing NAB
--------------

### Supported Platforms

- OSX 10.9 and higher
- Amazon Linux (via AMI)

Other platforms may work but have not been tested.


### Initial requirements

You need to manually install the following:

- [Python 2.7](https://www.python.org/download/)
- [pip](https://pip.pypa.io/en/latest/installing.html)
- [Numpy](http://www.numpy.org/num)
- [NuPIC](http://www.github.com/numenta/nupic) (Required only to run the Numenta detector)

##### Download this repository

    cd ~/
    git clone https://github.com/numenta/NAB.git

##### Install Python requirements

    cd NAB
    (sudo) pip install -r requirements.txt

This will install the additional required modules pandas and simplejson.  


### Usage

##### Run NAB

    cd /path/to/nab
    python run.py
    python setup.py develop (for now)

This will produce results files for the anomaly detection methods. Included in the repo are the Numenta anomaly detection method, as well as methods from the [Etsy Skyline](https://github.com/etsy/skyline) anomaly detection library, and a random detector. This will also pass those results files to the scoring script to generate final NAB scores.

For details on how to run your own detector please see the [NAB Entry Points diagram](https://github.com/numenta/NAB/wiki#nab-entry-diagram) in the wiki.

To view a description of the command line options please enter

	python run.py --help 

Once NAB is finalized (not yet!) to replicate results exactly you will need a specific version of NuPIC:
    
    cd /path/to/nupic/
    git checkout -b nab {TAG NAME}

Then follow build directions in the [NuPIC "README.md"](https://github.com/numenta/nupic/blob/master/README.md).

#### Data

##### Data and results files

This repo contains a corpus of 32 data files of time-series data. The format of the CSV files is specified in Appendix G of the [NAB Whitepaper](https://github.com/numenta/NAB/wiki#nab-whitepaper). The detector under test will read in, and be scored on, all data files in the corpus. The format of results files is also specified in the whitepaper posted in the wiki.

##### Data visualizer

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
