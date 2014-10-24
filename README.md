### Under Construction

#### This repo is under heavy, active revision. The code does not work yet. Browse, but don't judge. :)

The Numenta Anomaly Benchmark
-----------------------------

This repository contains the data and scripts necessary to replicate the
results in the forthcoming Numenta Anomaly Benchmark (NAB) paper.

We hope you will compare these results with your own anomaly detection methods.
Competitive results tied to open source code will be listed here. Let us know
about your work by submitting a pull request.

### Corpus

The NAB corpus of timeseries datasets is designed to provide data for research
in streaming anomaly detection. It is comprised of both artificial and
real-world timeseries data containing labeled anomalous periods of behavior.

All data are ordered, timestamped, single-valued metrics collected at 5 minute
intervals.

Much of the real-world data are values from AWS server metrics as collected by 
the [AmazonCloudwatch service](https://aws.amazon
.com/documentation/cloudwatch/). Example
metrics include CPU Utilization, Network Bytes In, and Disk Read Bytes. There
are also real world sensor readings from some large machines. 

All data is included in the repository. We are actively searching for more data

#### Task

Detect anomalous behavior in streaming data in real-time and provide *useful*
alerts.

You must be able to handle streaming data.

Post-hoc analysis is insufficient for this task. All classifications must
be done as if the data is being presented for the first time, in real time.

You must be able to provide a response in a reasonable amount of time.

This benchmark is representative of a task in human time-scales. Per-record
classification should take place in less than 5 minutes. Anomaly detection
should happen as quickly as possible following the onset of an anomaly.

You must minimize the cost of using your detection technique.

It is insufficient to just catch all anomalies. A high false-positive rate will
reduce or eliminate an institution's willingness to use your technique.

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
- [NuPIC](http://www.github.com/numenta/nupic) (Source Required)

It is also assumed you have a full checkout and working version of NuPIC 
by this point.

##### Download this repository

    cd ~/
    git clone https://github.com/numenta/NAB.git

##### Install Python requirements

    cd NAB
    (sudo) pip install -r requirements.txt

This will install a bunch of requirements, such as pandas and simplejson.  


### Usage

    cd /path/to/nab
    python setup.py develop (for now)
    python run.py

This will produce results files for the Numenta anomaly detection method as well
as baseline results using methods from the [Etsy
Skyline](https://github.com/etsy/skyline) anomaly detection library. This will
also pass those results files to the analyze_results.py script to
generate final scores.

Once NAB is finalized (not yet!) to replicate results exactly you will need a 
specific version of NuPIC:
    
    cd /path/to/nupic/
    git checkout -b nab {TAG NAME}

Then follow build directions in the NuPIC `README.md`.

#### Data format

##### Input data files

This is the file format for each datafile in the corpus.

- All files MUST be in CSV format
- All files MUST have exactly one header row
- The header row MUST have the following fields
    - "timestamp"
        - The time of the end of the metric collection window
        - e.g 2014-04-01 12:00:00.000000 is values collected between
            - 2014-04-01 11:55:00.000000
            - 2014-04-01 12:00:00.000000
    - "value"
        - The collected metric, e.g. CPUUtilization percent
    - "label"
        - This is ground truth for the class of a record.
- Header rows MAY have other fields as well. These are ignored.
- Values in the "timestamp" column MUST follow this format
    - YYYY-MM-DD HH:MM:SS.s
    - e.g. 2014-04-01 00:00:00.000000
- Metric values in the "value" column MUST be either
    - floats
    - integers (these will be converted to floats internally)
- Values in the "label" column MUST be either
    - 0     - This record is known to be non-anomalous
    - 0.5   - This record's class is ambiguous
    - 1     - This record is known to be anomalous
- Each record MUST represent an equal amount of time
- Records MUST be in chronological order
- Records MUST be continuous such that there are no missing time steps

