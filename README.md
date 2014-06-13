The Numenta Anomaly Benchmark
-----------------------------

This is the companion repository for the upcoming anomaly detection benchmark
paper written by Numenta. It contains all of the relevant data and data
processing scripts to replicate the results in the paper.

We hope you will compare these results with your own anomaly detection methods.
Competative results tied to open source code will be listed here. Let us
know about your work by submitting a pull request or emailing INSERT EMAIL LATER.

Finally we hope you will help improve these results by contributing to the
[Numenta Platform for Intelligent Computing (NuPIC)](https://github.com/numenta/nupic).

### Corpus

The NAB corpus of timeseries datasets is designed to provide data for research
in streaming anomaly detection. It is comprised of both artificial and
real-world timeseries data containing labeled anomalous periods of behavior.

All data are ordered, timestamped, single-valued metrics collected at 5 minute
intervals.

Realworld data are values from AWS server metrics as collected by the [Amazon
Cloudwatch service](https://aws.amazon.com/documentation/cloudwatch/). Example
metrics include CPU Utilization, Network Bytes In, and Disk Read Bytes.

#### Download

[numenta_anomaly_benchmark_corpus.zip](https://aws.amazon.com/documentation/cloudwatch/)

#### Task

Detect anomalous behavior in streaming data in real-time.

As noted in the paper, the task of streaming anomaly detection is challenging
for several reasons which place significant constraints on the allowable
methods.

You must be able to provide a reliable anomaly score with minimal prior
knowledge of the data. There is hardly ever a single 'normal' set of statistics
for a streaming dataset and those statistics change constantly.

You must be able to provide a classification in a reasonable amount of time.
This benchmark is representative of a task in human time-scales. Microsecond
responses are not required, but hour-long determinations are unacceptable. Here
it is expected that record classification should take place in far less than 5
minutes. (NOTE: Should we include this? We do well here, but its not primary.)

You must minimize the impact, which is often financial, on the institution
making use of your detection technique. It is insufficient to just catch all
anomalies as a high false-positive rate can reduce or eliminate an institution's
willingness to use your technique.

Each of these constraints is handled explicitly by the code in this repository.
We hope this will allow you to quickly get a useful, real-world evaluation of
your anomaly detection method.

### Supported Platforms

- OSX 10.9 and higher

Other platforms may work but have not been tested. It is expected that several
flavors of Linux will be supported. Windows will not be supported for
replicating results but will be supported for analyzing your own. This is
because the code to replicate our results depends on NuPIC, which does not
support Windows at this time.

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

In addition we provide all of the scripts we used to generate our results using
CLA. To replicate those results you will also need to install:

- [NuPIC](http://www.github.com/numenta/nupic)

#### Optional Extras

- [Plotly](https://plot.ly/)

If you would like these scripts to plot results you can sign up for a free
Plot.ly account and install their Python library. (If you use pip to install
from requirements.txt below this will be installed automatically.)

After you have signed up you will need to add your username and API key to your
environment.

    export PLOTLY_USER_NAME='{YOUR PLOTLY USERNAME}'
    export PLOTLY_API_KEY='{YOUR API KEY}'

You can then add the --plot option to any python script to visualize output.

### Installation

#### To Analyze Your Results Only

It is assumed you have git, python 2.7 and pip installed by this point.

##### Download this repository

    cd ~/
    git clone https://github.com/numenta/NAB.git

##### Install Python Requirements

    cd nab
    (sudo) pip install -r requirements.txt

#### To Replicate Our Results

It is assumed you have NuPIC installed by this point.

##### Update NuPIC to the correct commit to replicate the paper's results

    cd /path/to/nupic/
    git checkout -b nab {TAG NAME}

Then follow build directions in the NuPIC `README.md`.

### EC2 Image

We also provide an Amazon Machine Image (AMI) from which you can launch
an EC2 instance with all requirements and this repository pre-installed.

ami-9faddeaf

### Usage

#### Analyze Your Results

If you have used the NAB corpus with your own anomaly detection method you can
directly compare your results to ours with the provided script.

    cd /path/to/nab
    python analyze_results.py -i /path/to/your/results.csv

Please see "Results Files" below for the expected format of these files.

#### Replicate Our Results

    cd /path/to/nab
    python run_benchmark.py

This will produce results files for the CLA anomaly detection method as well as
baseline results using methods from the [Etsy
Skyline](https://github.com/etsy/skyline) anomaly detection library. This will
also pass those results files to the analyze_results.py script as above to
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
    - 0.5   - This record's class is indeterminate
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
    - 0.5   - This record's class is indeterminate
    - 1     - This record is known to be anomalous
- Each record MUST correspond, one for one, to records in their input data file


## TODO

- Make note of best tag to use
- Add in threshold and adaptive threshold based measures for comparison
- Code is duplicated between GEF and analyze_results - decide where it belongs
- Two skyline algorithms use scipy code
    - grubbs requires use of the inverse survival function from SciPy
    - ks_test requires ks_2samp
- Should the calculation of min/max be a part of each detector?
- for AnomalyDetector remove outputDir and infer it from outputFile which 
  should be a path
- gef charts of run_anomaly output need to reflect the proper length of the 
  probationary period
- Remove results from AMI before creating final.
- Move to CentOS AMI starting from stage 2
- Upload a zipped version of data to S3 for quick download.
    - Update link in README above
- Update realAWSCloudwatch data to proper NAB format
- Label viewing of NAB input file type is not behaving properly
- Add 0.5s as probationary period to all datasets
- Data processing script
  - verify input data format
  - adjust probationary period length
  - adjust transition period length
  - expand acronyms?

#### Labeling Rules

- Point anomalies are labeled
  - PA
- Anomalous periods are labeled
  - APB - Anomalous Period Begins
  - APE - Anomalous Period Ends
- Transition periods are labeled
  - If a new, stable pattern looks like is being established, this transition noted
    - TPB - Transition Period Begins
  - If an expected transition does *not* occur, then the transition period still applies (e.g. art_daily_nojump.csv)
  - The first two hours of a new, stable pattern will be labeled anomalous
  - After two hours (24 records) the end of the transition period will be noted
    - TPE - Transition Period Ends

##### Anomalous Periods

- A new pattern is no longer anomalous after 2 hours
  - 24 records

