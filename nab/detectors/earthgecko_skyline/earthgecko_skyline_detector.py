import time
import sys
from nab.detectors.base import AnomalyDetector

from nab.detectors.earthgecko_skyline.algorithms import (
    histogram_bins,
    first_hour_average,
    stddev_from_average,
    mean_subtraction_cumulation,
    median_absolute_deviation,
    stddev_from_moving_average,
    least_squares)

####
# USER SETTINGS see README.md

# The grubbs and ks_test algorithms do not run by default they are excluded.
GRUBBS_KS_TEST_ENABLED = False
# GRUBBS_KS_TEST_ENABLED = True

# The EXPIRATION_TIME is the number of seconds which should have passed after an
# anomaly has been detected, before the detector scores another anomaly on the
# time series
# EXPIRATION_TIME = 1800  # 30m
# EXPIRATION_TIME = 3600  # 1h
# EXPIRATION_TIME = 7200  # 2h
# EXPIRATION_TIME = 14400  # 4h - most realistic maximum
# EXPIRATION_TIME = 21600  # 6h
# EXPIRATION_TIME = 25200  # 7h
EXPIRATION_TIME = 43200  # 12h - best NAB score
# EXPIRATION_TIME = 50400  # 14h - NAB score starts to decrease at > 14h

# The CONSENSUS is the number of algorithms that must trigger in order for a
# data point to be considered as anomalous.
# CONSENSUS of 5 is used when the grubbs and ks_test algorithms are not enabled
CONSENSUS = 5
# CONSENSUS of 7 is used when the grubbs and ks_test algorithms are enabled
# CONSENSUS = 7

# Only use a sample of the data points of long time series
SHORTEN_TIMESERIES = False
# SHORTEN_TIMESERIES = True
# Based on 5 minute resolution data shorten to 7 days (513 data points) + 4 hrs
# (60 data points) either side if SHORTEN_TIMESERIES is True
SHORTEN_TO_DATAPOINS = 633

# Use the NAB averageScore method and not CONSENSUS - long running, all algos,
# all data points.
AVERAGESCORE = False
# AVERAGESCORE = True

# Enable debug logging
LOCAL_DEBUG = False
LOCAL_DEBUG_PATH = '/tmp'

if GRUBBS_KS_TEST_ENABLED:
    try:
        import scipy
        scipy_version = scipy.version.version
        if scipy_version != '1.1.0':
            print(('To run grubbs and ks_test scipy==1.1.0 is required, scipy %s is installed' % scipy_version))
            sys.exit(1)
    except:
        print('To run grubbs and ks_test scipy==1.1.0 is required')
        sys.exit(1)
    try:
        import statsmodels
        statsmodels_version = statsmodels.version.version
        if statsmodels_version != '0.8.0':
            print(('To run grubbs and ks_test statsmodels==0.8.0 is required, statsmodels %s is installed' % statsmodels_version))
            sys.exit(1)
    except:
        print('To run grubbs and ks_test statsmodels==0.8.0 is required')
        sys.exit(1)
    from nab.detectors.earthgecko_skyline.skyline_algorithms import (
        grubbs,
        ks_test)


class EarthgeckoSkylineDetector(AnomalyDetector):
    """
    Detects anomalies using earthgecko Skyline's ensemble of algorithms.
    """

    def __init__(self, *args, **kwargs):

        # Initialize the parent
        super(EarthgeckoSkylineDetector, self).__init__(*args, **kwargs)

        # Store our running history
        self.timeseries = []

        # Store our running history with the anomalyScore for evaluation in
        # terms of expiration
        self.timeseries_and_anomalyscores = []

        self.recordCount = 0
        # These algorithms are ordered in terms of efficiency to achieve CONSENSUS
        # see https://earthgecko-skyline.readthedocs.io/en/latest/analyzer-optimizations.html#algorithm-benchmarks
        if GRUBBS_KS_TEST_ENABLED:
            self.algorithms = [
                histogram_bins,
                first_hour_average,
                stddev_from_average,
                grubbs,
                ks_test,
                mean_subtraction_cumulation,
                median_absolute_deviation,
                stddev_from_moving_average,
                least_squares,
            ]
        else:
            self.algorithms = [
                histogram_bins,
                first_hour_average,
                stddev_from_average,
                mean_subtraction_cumulation,
                median_absolute_deviation,
                stddev_from_moving_average,
                least_squares,
            ]

        self.LOCAL_DEBUG = LOCAL_DEBUG
        if LOCAL_DEBUG:
            rundate = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.debug.txt', 'w') as debugfile:
                debugfile.write('# %s\n' % rundate)
            with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.ts.debug.txt', 'w') as tsdebugfile:
                tsdebugfile.write('# %s\n' % rundate)
            with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.consensus.false.debug.txt', 'w') as debugfile:
                debugfile.write('# %s\n' % rundate)
            with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.debug.anomalies.txt', 'w') as debugfile:
                debugfile.write('# %s\n' % rundate)
            with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.score.txt', 'w') as scorefile:
                scorefile.write('# %s\n' % rundate)

    def handleRecord(self, inputData):
        """
        Returns a list [anomalyScore].
        """

        score = 0.0

        # Determine the resolution of the time series being analysed as all NAB
        # data sets are not equal, most have a 5 minute resolution but some
        # have more than 5 mins.  Not done in this round of testing, but
        # leaving the mention here for any future

        # Use Skyline unix timestamps
        # nabinputRow = [inputData["timestamp"], inputData["value"]]
        ts = inputData["timestamp"]

        # Convert the Timestamp object to a epoch timestamp
        timestamp = ts.strftime('%s')

        inputRow = [int(timestamp), inputData["value"]]
        self.timeseries.append(inputRow)
        if self.LOCAL_DEBUG:
            nabinputRow = [inputData["timestamp"], inputData["value"]]
            with open(LOCAL_DEBUG_PATH + '/nab.debug.txt', 'a') as debugfile:
                debugfile.write(str(inputData))
            with open(LOCAL_DEBUG_PATH + '/nab.ts.debug.txt', 'w') as tsdebugfile:
                tsdebugfile.write(str(self.timeseries))

        # Handle EXPIRATION_TIME.  NAB skyline_detector does not take into
        # account Skyline's expiration concept, which reduces noise.
        # So if an anomaly has been seen in the last EXPIRATION_TIME seconds,
        # do not process and return an anomalyScore of 0.0
        process_datapoint = True
        expiration_timestamp = int(timestamp) - EXPIRATION_TIME
        if self.timeseries_and_anomalyscores:
            for ts, datapoint, anomalyscore in reversed(self.timeseries_and_anomalyscores):
                if int(ts) > expiration_timestamp:
                    if int(anomalyscore) == 1:
                        process_datapoint = False
                        break
                else:
                    break
        if not process_datapoint:
            return [score]

        triggered_algorithms = []
        number_of_algorithms_run = 0
        number_of_algorithms = len(self.algorithms)
        maximum_false_count = number_of_algorithms - CONSENSUS + 1
        consensus_possible = True
        number_of_algorithms_triggered = 0

        if process_datapoint:
            if SHORTEN_TIMESERIES:
                if len(self.timeseries) > SHORTEN_TO_DATAPOINS:
                    analyse_timeseries = self.timeseries[-SHORTEN_TO_DATAPOINS:]
                else:
                    analyse_timeseries = self.timeseries
            else:
                analyse_timeseries = self.timeseries

            for algo in self.algorithms:
                if not AVERAGESCORE:
                    if number_of_algorithms_triggered >= CONSENSUS:
                        continue
                else:
                    consensus_possible = True
                if consensus_possible:
                    number_of_algorithms_run += 1
                    algorithm_result = algo(analyse_timeseries, self.LOCAL_DEBUG, LOCAL_DEBUG_PATH)
                    if algorithm_result:
                        triggered_algorithms.append(algo)
                        # score += algorithm_result
                        score += 1
                    if self.LOCAL_DEBUG:
                        scoreline = 'algo_result=%s' % (str(algorithm_result))
                        with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.score.txt', 'a') as scorefile:
                            scorefile.write(scoreline + '\n')
                else:
                    algorithm_result = False
                number_of_algorithms_triggered = len(triggered_algorithms)
                false_count = number_of_algorithms_run - number_of_algorithms_triggered
                if false_count >= maximum_false_count:
                    consensus_possible = False
                    if self.LOCAL_DEBUG:
                        writeline = 'consensus_possible - False - number_of_algorithms_triggered: %s, number_of_algorithms_run: %s' % (str(number_of_algorithms_triggered), str(number_of_algorithms_run))
                        with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.consensus.false.debug.txt', 'a') as debugfile:
                            debugfile.write(writeline + '\n')

        if self.LOCAL_DEBUG:
            scoreline = '%s,score=%s' % (str(inputRow), str(score))
            with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.score.txt', 'a') as scorefile:
                scorefile.write(scoreline + '\n')

        if number_of_algorithms_triggered >= CONSENSUS:
            anomalyScore = 1.0
            if self.LOCAL_DEBUG:
                line = 'anomaly - %s algorithms triggered - %s for %s - %s\n' % (str(number_of_algorithms_triggered), str(triggered_algorithms), str(inputRow), str(nabinputRow))
                with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.debug.anomalies.txt', 'a') as debugfile:
                    debugfile.write(line)
        else:
            anomalyScore = 0.0
            averageScore = 0.0
        if score:
            averageScore = score / (number_of_algorithms_run + 1)
        else:
            averageScore = 0.0

        new_inputRow = [int(timestamp), inputData["value"], anomalyScore]
        self.timeseries_and_anomalyscores.append(new_inputRow)

        if self.LOCAL_DEBUG:
            if not process_datapoint:
                scoreline = 'expiration skipped - %s' % str(new_inputRow)
                with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.score.txt', 'a') as scorefile:
                    scorefile.write(scoreline + '\n')

        anomalyScoreline = 'anomalyScore=%s' % (str(anomalyScore))
        averageScoreline = 'averageScore=%s' % (str(averageScore))

        if self.LOCAL_DEBUG:
            with open(LOCAL_DEBUG_PATH + '/nab.earthgecko_skyline.score.txt', 'a') as scorefile:
                scorefile.write(anomalyScoreline + '\n')
                scorefile.write(averageScoreline + '\n')

        if AVERAGESCORE:
            return [averageScore]
        return [anomalyScore]
