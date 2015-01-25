### Under Construction

#### This repo is under active revision. The code runs but is not yet complete, so please don't judge. :)

The Numenta Anomaly Benchmark
-----------------------------

Welcome. This repository contains the data and scripts necessary to replicate the
results in the forthcoming Numenta Anomaly Benchmark (NAB) paper. It also provides the tools to run NAB to score your own anomaly detection algorithms. Competitive results tied to open source code will be posted here on the Scoreboard. Let us know about your work by submitting a pull request.

#### Corpus

The NAB corpus of timeseries datasets is designed to provide data for research
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

Detect anomalous behavior in streaming data in real-time and provide *useful* alerts.

Your anomaly detector must be able to handle streaming data. Post-hoc analysis is insufficient for this task. All classifications must
be done as if the data is being presented for the first time, in real time. Anomalies must be detected within a reasonable amount of time.

This benchmark is representative of a task in human time-scales. Per-record classification should take place in less than 5 minutes. Anomaly detection should happen as quickly as possible following the onset of an anomaly.

It is insufficient to just catch all anomalies. A high false-positive rate will reduce or eliminate an institution's willingness to use your technique. You must minimize the cost of using your detection technique.

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

This will produce results files for the desired anomaly detection methods; the user is prompted which algorithm(s) to run. Included in the repo are the Numenta anomaly detection method, as well as methods from the [Etsy Skyline](https://github.com/etsy/skyline) anomaly detection library, and a random detector. This will also pass those results files to the analyze_results.py script to generate final NAB scores.

##### Run your detector

To run your own detector (named 'DUT' for detector under test), first create a folder in the nab detectors directory:

    cd /path/to/nab/detectors
    mkdir DUT

This folder should contain all scripts necessary to run your detector. To run properly on the NAB corpus, your algorithm must meet the specs laid out below in the "Detector Results datafiles" section.

Running NAB as instructed above will allow you the option of selecting which detector(s) to run. When prompted, enter `DUT` and you’re good to go!

Once NAB is finalized (not yet!) to replicate results exactly you will need a specific version of NuPIC:
    
    cd /path/to/nupic/
    git checkout -b nab {TAG NAME}

Then follow build directions in the [NuPIC "README.md"](https://github.com/numenta/nupic/blob/master/README.md).

#### Data format

##### Raw input data files

This repo contains a corpus of 35 file of time-series data, in the format below. The detector under test will read in all datafiles in the corpus.

- CSV format
- One header row
- Fields for "timestamp" and "value"
    - "timestamp"
        - The time of the end of the metric collection window
        - e.g 2014-04-01 12:00:00.000000 is values collected between
            - 2014-04-01 11:55:00.000000
            - 2014-04-01 12:00:00.000000
    - "value"
        - The collected metric, e.g. CPUUtilization percent
        - MUST be either floats or integers (converted to floats internally)
- Each record MUST represent an equal amount of time
- Records MUST be in chronological order
- Records MUST be continuous such that there are no missing time steps

##### Detector results data files

The detector under test will output a results file for each datafile in the corpus. This is the format:

- All files MUST be in CSV format
- All files MUST have exactly one header row
- The header row MUST have the following fields
    - "timestamp", MUST follow this format:
	    - YYYY-MM-DD HH:MM:SS.s
    	- e.g. 2014-04-01 00:00:00.000000
    - "value": same format as input data files
    - "label"
        - This is ground truth for the class of a record
        - Values are either:
            - 0: This record is known to be non-anomalous
		    - 0.5: This record's class is ambiguous
    		- 1: This record is known to be anomalous
- Header rows MAY have other fields as well. These are ignored by the NAB scorer.
- Each record MUST represent an equal amount of time
- Records MUST be in chronological order
- Records MUST be continuous such that there are no missing time steps

##### Data visualizer

There is currently a simple data visualizer available, usefule in hand labeling datasets. To use it do the following:

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
