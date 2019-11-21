# Numenta and NumentaTM detectors

This directory holds the Python 2 code required to run the `numenta` and
`numentaTM` detectors against the NAB data. In 2019 the main body of the
benchmark's code was ported to Python 3 however these detectors rely on NuPIC
which is Python 2 only.

This code can be used to replicate results listed on the scoreboard of
the main repository for the following detectors:

    numenta
    numentaTM

## Installation

### Docker

Both these detectors are also provided within a docker image, available with `docker pull numenta/nab:py2.7`.

### Assumptions

We assume you have a working version of Python 3 installed as your default Python.
If your default system Python is still Python 2 you can skip the virtual environment
creation below.

### Requirements to install

- [Python 2.7](https://www.python.org/download/)
- [Virtualenv](https://pypi.org/project/virtualenv/)

### Install a virtual environment

Create a new Python 2 virtual environment in this directory.

`virtualenv -p path/to/python2 env`

On Windows this might be:

`virtualenv -p C:\Python27\python.exe env`

Activate that virtual environment.

`./env/Scripts/activate`

or

`env\Scripts\activate.bat` on Windows.

Confirm you have a local Python 2

```
$ python
Python 2.7.13 (v2.7.13:a06454b1afa1, Dec 17 2016, 20:53:40) [MSC v.1500 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

### Install detectors

`cd /path/to/NAB/`
`pip install nupic`
`python nab/detectors/numenta/setup.py develop`

## Usage

### Detection

This directory contains a modified version of the `run.py` script which exists
in the main NAB directory. It can be used to run *detection* only using the
`numenta` and `numentaTM` detectors against NAB data.

By default it will run both `numenta` and `numentaTM` detectors and output
results to the main NAB/results directory.

`python2 run.py`

Note: By default `run.py` tries to use all the cores on your machine. The above
command should take about 20-30 minutes on a current powerful laptop with 4-8
cores.

To run only one of the detectors use the `-d` option:

`python2 run.py -d numenta`

To see all options of this script type:

`python2 run.py --help`

### Optimizing, Scoring and Normalizing

Once you have run either of the detectors herein against the NAB data you will need
to exit the Python 2 virtual environment and move into the main NAB directory.

```
(env) /NAB/nab/detectors/numenta
$ deactivate                                                          
/NAB/nab/detectors/numenta      
$ cd ../../../
/NAB
$
```

Then follow the instructions in the main README to run optimization, scoring, and normalization, e.g.:

`python run.py -d numenta,numentaTM --optimize --score --normalize`

### Run a subset of NAB data files

For debugging it is sometimes useful to be able to run your algorithm on a
subset of the NAB data files or on your own set of data files. You can do that
by creating a custom `combined_windows.json` file that only contains labels for
the files you want to run. This new file should be in exactly the same format as
`combined_windows.json` except it would only contain windows for the files you
are interested in.

**Example**: an example file containing two files is in
`labels/combined_windows_tiny.json`. (Under of the main NAB directory) The
following command shows you how to run NAB on a subset of labels:

    python2 run.py -d numenta --detect --windowsFile labels/combined_windows_tiny.json

This will run the `detect` phase of NAB on the data files specified in the above
JSON file. Note that scoring and normalization are not supported with this
option. Note also that you may see warning messages regarding the lack of labels
for other files. You can ignore these warnings.
