The Numenta Anomaly Benchmark
-----------------------------

This repository contains the data and scripts neccessary to replicate the
results in the Numenta Anomaly Benchmark paper.

We hope you will compare these results with your own anomaly detection methods.
Competative results tied to open source code will be listed here. Let us know
about your work by submitting a pull request.

### Corpus

The NAB corpus of timeseries datasets is designed to provide data for research
in streaming anomaly detection. It is comprised of both artificial and
real-world timeseries data containing labeled anomalous periods of behavior.

All data are ordered, timestamped, single-valued metrics collected at 5 minute
intervals.

Real-world data are values from AWS server metrics as collected by the [Amazon
Cloudwatch service](https://aws.amazon.com/documentation/cloudwatch/). Example
metrics include CPU Utilization, Network Bytes In, and Disk Read Bytes.

#### Download

[numenta_anomaly_benchmark_corpus.zip](https://s3.amazonaws.com/numenta.datasets/nab/numenta_anomaly_benchmark_corpus_c97b56.zip)

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

Cost scoring is [covered in detail](#scoring-rules) below. It is *highly*
recommended that you understand the scoring logic and code as it is essential to
good performance on this benchmark.

### EC2 Image

We provide an Amazon Machine Image (AMI) from which you can launch
an EC2 instance with all requirements and this repository pre-installed.

ami-299be419

On an m3.2xlarge the full benchmark takes around 8 minutes to run.

### Supported Platforms

- OSX 10.9 and higher
- Amazon Linux (via AMI)

Other platforms may work but have not been tested.

### Requirements

We provide scripts that will allow you to generate results under the same
constraints used in the Numenta paper. To use that code you will need to have
the following installed.

- [Git](http://git-scm.com/book/en/Getting-Started-Installing-Git)
- [Python 2.7](https://www.python.org/download/)
- [pip](https://pip.pypa.io/en/latest/installing.html)
- [Numpy](http://www.numpy.org/num)
- [Pandas](http://pandas.pydata.org/)
- [PyYaml](http://pyyaml.org/)
- [NuPIC](http://www.github.com/numenta/nupic) (Source Required)

### Local Installation

It is assumed you have git, python 2.7 and pip installed by this point.

It is also assumed you have a full checkout of the NuPIC source by this point.

##### Download this repository

    cd ~/
    git clone https://github.com/numenta/NAB.git

##### Install Python Requirements

    cd nab
    (sudo) pip install -r requirements.txt

##### Update NuPIC to the correct commit

    cd /path/to/nupic/
    git checkout -b nab {TAG NAME}

Then follow build directions in the NuPIC `README.md`.

### Usage

#### Replicate Our Results

    cd /path/to/nab
    python run_benchmark.py

This will produce results files for the Numenta anomaly detection method as well
as baseline results using methods from the [Etsy
Skyline](https://github.com/etsy/skyline) anomaly detection library. This will
also pass those results files to the analyze_results.py script to
generate final scores.

#### Data Format

##### Input Data Files

This is the file format for each dataset in the corpus.

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

##### Results Files

This is the file format that will be output by run_anomaly.py and can
be consumed by analyze_results.py

- All files MUST be in CSV format
- All files MUST have exactly one header row
- The header row MUST have the following fields
    - "timestamp"
        - This ties each result record to it's input record
    - "anomaly_score"
        - This is the output of your detection technique for each record
    - "label"
        - This is ground truth for the class of a record.
- Header rows MAY have other fields as well. These are ignored.
- Values in the "timestamp" column MUST follow this format
    - YYYY-MM-DD HH:MM:SS.s
    - e.g. 2014-04-01 00:00:00.000000
- Values in the "anomaly_score" column MUST be
    - floats between 0.0 and 1.0
- Values in the "label" column MUST be either
    - 0     - This record is known to be non-anomalous
    - 0.5   - This record's class is ambiguous
    - 1     - This record is known to be anomalous
- Each record MUST correspond, one for one, to records in their input data file

### Evalutation

#### Labeling Key
 
- PA - Point anomaly
- APB - Anomalous Period Begins
- APE - Anomalous Period Ends
- TPB - Transition Period Begins
  - If a new, stable pattern looks like is being established the first two 
    hours will be labeled ambiguous.
    - However if the stable pattern is one we have seen before it will
      be labeled non-anomalous.
- TPE - Transition Period Ends

#### Scoring Rules

These rules are implemented in confusion_matrix.py. They reflect real-world
requirements for a production anomaly detection system.

- For each record check if it is labeled (ground truth) as an anomaly
- If it is an anomaly
  - A detector has ALLOWED records to catch the anomaly
  - For each record that follows the start of the anomaly where the anomaly is 
    not caught, there is a small penalty (LAG)
  - If the detector catches the anomaly, this is a True Positive
    - Once an anomaly has been flagged there is a SUPRESSION period
    - To avoid spamming the end user a detector should not flag other records 
      as anomalous during the SUPPRESSION period
    - If a detector flags one *or more* additional records during a SUPPRESSION 
      period, it is a False Positive (SPAM)
      - This reflects the binary nature of Spam. Once the useful detection has 
        been made everything else is spam. Lots of spam is only marginally 
        worse than any spam.
    - If a record is not flagged as an anomaly in the SUPPRESSION period this 
      is a True Negative
  - If ALLOWED records ellapse without the anomaly being caught it is a 
    False Negative
- If it is not an anomaly, and we're not in an ALLOWED period or in a 
  SUPRESSION period then:
  - If it is flagged as an anomaly it is a False Positive
  - Otherwise it is a True Negative

