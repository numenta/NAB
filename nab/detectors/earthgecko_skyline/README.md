earthgecko_skyline
------------------

This directory contains the code comprising of a port of the **most basic
analysis** method of the [earthgecko Skyline](https://github.com/earthgecko/skyline)
anomaly detection application that is suitable for benchmarking with the
Numenta Anomaly Benchmark (NAB).  Unfortunately Skyline's more advanced analysis
methods do not fit within the current NAB scope.

#### requirements.txt

In addition to the requirements.txt of NAB, **if** earthgecko_skyline is tested
with the grubbs and ks_test algorithms (disabled by default) the following
additional requirements are needed:

```
scipy==1.1.0
statsmodels==0.8.0
```

#### Overview

This detector differs from the skyline detector in a number of ways, which are
outlined here. The numenta NAB implementation of the Etsy skyline detector does
use the Etsy Skyline algorithms, however it is not a sound representation of the
Skyline mode of operation.  The primary differences being:

- The original implementation used a majority voting scheme to classify a record
  as anomalous. The NAB port improved the detector's performance by using the
  average of the algorithms' votes as an anomaly score.  This removed the
  context of CONSENSUS, even if it works a small bit better in the NAB tests
  using the average, it is not a true representation of how Skyline functions.
  In terms of real time analysis and operations of Skyline this average score
  method makes Skyline **vastly** less efficient due to Skyline algorithms being
  ranked and optimized (https://earthgecko-skyline.readthedocs.io/en/latest/analyzer-optimizations.html#algorithm-benchmarks)
- The NAB skyline implementation does not take into account or implement the
  ``EXPIRATION_TIME`` functionality in which anomaly alerts will not fire
  twice within ``EXPIRATION_TIME``, even if the time series triggers as
  anomalous again.  This is a very important feature in Skyline to ensure a
  lower number of FPs and FNs.

It most be noted that if the NAB Skyline implementation was configured
in a similar manner, it too would achieve similar scores to the
earthgecko_skyline detector.

This detector is a more realistic representation of a real world running Skyline
instance.  It must be noted that 2 Skyline algorithms have been excluded by
default to adhere to the NAB Contributions Criteria.  These are the grubbs and
ks_test algorithms as they are considered to be computationally inefficient to
process streaming data, i.e they are not O(N).

However for the purpose of getting the best NAB benchmark scores that could be
achieved, the default settings for the detector therefore are not reasonable
in terms of a real running Skyline instance, they are aimed at a high NAB score.

#### Configurable

By *default* the earthgecko_skyline_detector is configured to adhere to
NAB.  However the variables that can be tuned to test it in it's normal running
configuration (or test various different configs).  The variables are:

```python
GRUBBS_KS_TEST_ENABLED = False

# The EXPIRATION_TIME is the number of seconds which should have passed after an
# anomaly has been detected, before the detector scores another anomaly on the
# time series
EXPIRATION_TIME = 43200

# The CONSENSUS is the number of algorithms that must trigger in order for a
# data point to be considered as anomalous.
# CONSENSUS of 5 when the grubbs and ks_test algorithms are not enabled
CONSENSUS = 5
# CONSENSUS of 7 when the grubbs and ks_test algorithms are enabled
# CONSENSUS = 7

# Only use a sample of the data points of long time series
SHORTEN_TIMESERIES = False
# Based on 5 minute resolution data shorten to 7 days (513 data points) + 4 hrs
# (60 data points) either side
SHORTEN_TO_DATAPOINTS = 633

# Enable debug logging
LOCAL_DEBUG = False
LOCAL_DEBUG_PATH = '/tmp'
```

#### Running NAB on Ubuntu with a cp27mu compatible Python

In terms of Ubuntu, the Python version required to install the nupic package and
nupic-bindings is required to be compiled with ``--enable-unicode=ucs4``

Building a specific Python version from source to use with virtualenv requires
the following system dependencies:

- RedHat family

```bash
  yum -y install epel-release
  yum -y install autoconf zlib-devel openssl-devel sqlite-devel bzip2-devel \
    gcc gcc-c++ readline-devel ncurses-devel gdbm-devel compat-readline5 \
    freetype-devel libpng-devel python-pip wget tar git
```

- Debian family

```bash
  apt-get -y install build-essential
  apt-get -y install autoconf zlib1g-dev libssl-dev libsqlite3-dev libbz2-dev \
    libreadline6-dev libgdbm-dev libncurses5 libncurses5-dev libncursesw5 \
    libfreetype6-dev libxft-dev python-pip wget tar git
```

virtualenv is required and regardless of your OS as long as you have pip
installed you can install virtualenv.  virtualenv must be >= 15.0.1 and <16.0.0
due to some recent changes in pip, setuptools and virtualenv.  This is using
your system pip at this point only to install virtualenv.

```bash
  pip install 'virtualenv==15.2.0'
```

Build Python-2.7.15 (the minor version can be updated to a newer version if
there is one).  In this example Python and the Python virtualenv projects are
managed under /opt/python_virtualenv/versions and /opt/python_virtualenv/projects,
your user should own /opt/python_virtualenv/projects.

```bash
  sudo -i
  python_version="2.7.15"
  cp_version="2.7.15-cp27mu"
  mkdir -p "/opt/python_virtualenv/versions/${cp_version}"
  cd "/opt/python_virtualenv/versions/${cp_version}"
  wget -q https://www.python.org/ftp/python/${python_version}/Python-${python_version}.tgz
  tar -zxvf Python-${python_version}.tgz
  cd /opt/python_virtualenv/versions/${cp_version}/Python-${python_version}/
  ./configure --prefix=/opt/python_virtualenv/versions/${cp_version}/Python-${python_version} --enable-unicode=ucs4
  make
  make altinstall
  exit  # exit sudo
```
Create a NAB-py2715-cp27mu virtualenv

```bash
  PATH_TO_NAB=<PATH_TO_NAB>
  sudo mkdir -p /opt/python_virtualenv/projects
  sudo chown <YOUR_USERNAME>:<YOUR_USERNAME> /opt/python_virtualenv/projects
  cp_version="2.7.15-cp27mu"
  PYTHON_VERSION="2.7.15"
  PYTHON_MAJOR_VERSION="2.7"
  PYTHON_VIRTUALENV_DIR="/opt/python_virtualenv"  # NOTE if not using sudo, the user needs the appropriate permissions on this dir
  PROJECT="NAB-py2715-cp27mu"

  cd "${PYTHON_VIRTUALENV_DIR}/projects"
  virtualenv --python="${PYTHON_VIRTUALENV_DIR}/versions/${cp_version}/Python-$PYTHON_VERSION/bin/python${PYTHON_MAJOR_VERSION}" "$PROJECT"

  cd /opt/python_virtualenv/projects/$PROJECT
  source bin/activate
  bin/"pip${PYTHON_MAJOR_VERSION}" install -r $PATH_TO_NAB/requirements.txt
  # If you want to test all Skyline algorithms
  bin/"pip${PYTHON_MAJOR_VERSION}" install -r $PATH_TO_NAB/nab/detectors/earthgecko_skyline/requirements.txt

  deactivate
```

### Usage

##### Run earthgecko_skyline with NAB

```bash
  cd /opt/python_virtualenv/projects/$PROJECT
  source bin/activate
  cd $PATH_TO_NAB
  /opt/python_virtualenv/projects/$PROJECT/bin/"python${PYTHON_MAJOR_VERSION}" run.py -d earthgeckoSkyline
```

This will run the earthgecko_skyline_detector only and produce normalized
scores. Note that by default it uses all the cores on your machine. The above
command should take about 20-30 minutes on a current powerful laptop with 8
cores.  If NAB has been updated and is using sweep scoring and optimizing method
and not twiddle then this can be expected to run in ~7 minutes.

#### earthgecko_skyline Scoreboard

This is the earthgecko_skyline NAB scoreboard documenting the scores for Skyline
run under different parameters.

The best score achieved in terms of NAB is setting Skyline to not use the grubbs
and ks_test algorithm, using a ``CONSENSUS`` of 5 and setting the
``EXPIRATION_TIME`` to 43200.

An expiry setting of 43200 may seem extreme but seeing as NAB requires that:

> There must be no batch, or per data file, manual parameter tuning. The algorithm must be fully automated with a single set of parameters across all data files. Any further parameter tuning required by the algorithm must be done on the fly.

it has to be fixed for all.  In real world terms not all or probably any
metric namespaces would be configured with an ``EXPIRATION_TIME`` of 12 hours.  
However in terms of machine metrics this setting can actually be quite high 4hr
and is suited to some variable machine metrics as the scores do show.
This ``EXPIRATION_TIME`` achieves the highest NAB scores, hence it as used.

| Detector      | Standard Profile | Reward Low FP | Reward Low FN | runtime NAB twiddle | runtime sweep_scoring |
|---------------|------------------|---------------|---------------|---------------------|-----------------------|
|Perfect|100.0|100.0|100.0|||
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, consensus 5, expire 43200|58.20|46.20|63.80|00:32:51|00:06:51|
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, consensus 5, expire 50400|57.3|46.0|62.7||00:05:53|
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, consensus 5, expire 25200|56.4|42.3|62.6||00:07:26|
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, consensus 5, expire 21600|56.0|41.5|62.3||00:06:22|
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, CONSENSUS None using the NAB AVERAGESCORE method, expire 14400|54.5|39.4|61.3||00:35:27|
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, consensus 5, expire 14400|54.5|38.6|61.3|00:25:25|00:02:00|
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, consensus 5, expire 7200|52.8|34.4|60.5|00:33:58||
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, consensus 5, expire 3600|49.8|28.2|58.5|||
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - with grubbs,ks_test, consensus 7, expire 14400|47.4|40.0|51.1||00:06:36|
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - with grubbs,ks_test, consensus 7, expire 7200|47.0|39.1|50.9|||
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - with grubbs,ks_test, consensus 7, expire 3600|46.6|38.3|50.6|||
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, consensus 5, expire 1800|46.1|20.8|56.0|||
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - with grubbs,ks_test, shorten_ts, consensus 7, expire 1800|45.9|31.9|51.8|||
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - without grubbs,ks_test, consensus 5, expire 14400, shorten 633|44.3|20.5|54.0|||
|[earthgecko Skyline](https://github.com/earthgecko/skyline) - with grubbs,ks_test, consensus 8, expire 1800|28.9|26.3|30.5|||
|Null|0.0|0.0|0.0||||
