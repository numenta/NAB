"""
All algorithms from the original skyline implementation are included below.
"""

import numpy as np
import pandas
import traceback


def tail_avg(timeseries, debug, debug_path):
    """
    This is a utility function used to calculate the average of the last three
    datapoints in the series as a measure, instead of just the last datapoint.
    It reduces noise, but it also reduces sensitivity and increases the delay
    to detection.
    """
    if len(timeseries) < 3:
        return timeseries[-1][1]
    try:
        t = (timeseries[-1][1] + timeseries[-2][1] + timeseries[-3][1]) / 3
        return t
    except IndexError:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in tail_avg - trace - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return timeseries[-1][1]


def median_absolute_deviation(timeseries, debug, debug_path):
    """
    A timeseries is anomalous if the deviation of its latest datapoint with
    respect to the median is X times larger than the median of deviations.
    """
    try:
        series = pandas.Series([x[1] for x in timeseries])
        median = series.median()
        demedianed = np.abs(series - median)
        median_deviation = demedianed.median()
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in median_absolute_deviation 1st step - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None

    # The test statistic is infinite when the median is zero,
    # so it becomes super sensitive. We play it safe and skip when this happens.
    if median_deviation == 0:
        return False

    try:
        test_statistic = demedianed.iat[-1] / median_deviation
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in median_absolute_deviation - test_statistic - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None

    # Completely arbitary...triggers if the median deviation is
    # 6 times bigger than the median
    if test_statistic > 6:
        return True

    # As per https://github.com/etsy/skyline/pull/104 by @rugger74
    # Although never seen this should return False if not > arbitary_value
    # 20160523 @earthgecko
    return False


def first_hour_average(timeseries, debug, debug_path):
    """
    Calcuate the simple average over one hour, one day ago.
    A timeseries is anomalous if the average of the last three datapoints
    are outside of three standard deviations of this value.
    """

    try:
        # day = timedelta(days=1)
        # hour = timedelta(hours=1)
        # last_hour_threshold = timeseries[-1][0] - (day - hour)
        last_hour_threshold = timeseries[-1][0] - (86400 - 3600)
        series = pandas.Series([x[1] for x in timeseries if x[0] < last_hour_threshold])
        mean = (series).mean()
        stdDev = (series).std()
        t = tail_avg(timeseries, debug, debug_path)

        return abs(t - mean) > 3 * stdDev
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in first_hour_average - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None


def stddev_from_average(timeseries, debug, debug_path):
    """
    A timeseries is anomalous if the absolute value of the average of the lates
    three datapoint minus the moving average is greater than three standard
    deviations of the average. This does not exponentially weight the MA and so
    is better for detecting anomalies with respect to the entire series.
    """

    try:
        series = pandas.Series([x[1] for x in timeseries])
        mean = series.mean()
        stdDev = series.std()
        t = tail_avg(timeseries, debug, debug_path)

        return abs(t - mean) > 3 * stdDev
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in stddev_from_average - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None


def stddev_from_moving_average(timeseries, debug, debug_path):
    """
    A timeseries is anomalous if the absolute value of the average of the latest
    three datapoint minus the moving average is greater than three standard
    deviations of the moving average. This is better for finding anomalies with
    respect to the short term trends.
    """
    try:
        series = pandas.Series([x[1] for x in timeseries])
        expAverage = pandas.Series.ewm(series, ignore_na=False, min_periods=0, adjust=True, com=50).mean()
        stdDev = pandas.Series.ewm(series, ignore_na=False, min_periods=0, adjust=True, com=50).std(bias=False)
        return abs(series.iat[-1] - expAverage.iat[-1]) > 3 * stdDev.iat[-1]
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in stddev_from_moving_average - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None


def mean_subtraction_cumulation(timeseries, debug, debug_path):
    """
    A timeseries is anomalous if the value of the next datapoint in the
    series is farther than three standard deviations out in cumulative terms
    after subtracting the mean from each data point.
    """

    try:
        series = pandas.Series([x[1] if x[1] else 0 for x in timeseries])
        series = series - series[0:len(series) - 1].mean()
        stdDev = series[0:len(series) - 1].std()
        return abs(series.iat[-1]) > 3 * stdDev
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in mean_subtraction_cumulation - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None


def least_squares(timeseries, debug, debug_path):
    """
    A timeseries is anomalous if the average of the last three datapoints
    on a projected least squares model is greater than three sigma.
    """

    try:
        # x = np.array([(t[0] - datetime(1970, 1, 1)).total_seconds() for t in timeseries])
        x = np.array([t[0] for t in timeseries])
        y = np.array([t[1] for t in timeseries])
        A = np.vstack([x, np.ones(len(x))]).T

        # @modified 20180910 - Task #2588: Update dependencies
        # Changed in version numpy 1.14.0: If not set, a FutureWarning is given.
        # The previous default of -1 will use the machine precision as rcond
        # parameter, the new default will use the machine precision times
        # max(M, N). To silence the warning and use the new default, use
        # rcond=None, to keep using the old behavior, use rcond=-1.
        # Tested with time series - /opt/skyline/ionosphere/features_profiles/stats/statsd/processing_time/1491468474/stats.statsd.processing_time.mirage.redis.24h.json
        # new rcond=None resulted in:
        # np.linalg.lstsq(A, y, rcond=None)[0]
        # >>> array([3.85656116e-11, 2.58582310e-20])
        # Original default results in:
        # np.linalg.lstsq(A, y, rcond=-1)[0]
        # >>> array([ 4.10251589e-07, -6.11801949e+02])
        # Changed to pass rcond=-1
        # m, c = np.linalg.lstsq(A, y)[0]
        # BUT HERE IN NAB with numpy==1.11.2 revert back to old format
        # m, c = np.linalg.lstsq(A, y, rcond=-1)[0]
        m, c = np.linalg.lstsq(A, y)[0]

        errors = []
        # Evaluate append once, not every time in the loop - this gains ~0.020 s on
        # every timeseries potentially @earthgecko #1310
        append_error = errors.append

        for i, value in enumerate(y):
            projected = m * x[i] + c
            error = value - projected
            # errors.append(error) # @earthgecko #1310
            append_error(error)

        if len(errors) < 3:
            return False

        std_dev = np.std(errors)
        t = (errors[-1] + errors[-2] + errors[-3]) / 3

        return abs(t) > std_dev * 3 and round(std_dev) != 0 and round(t) != 0
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in least_squares - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None


def histogram_bins(timeseries, debug, debug_path):
    """
    A timeseries is anomalous if the average of the last three datapoints falls
    into a histogram bin with less than 20 other datapoints (you'll need to tweak
    that number depending on your data)

    Returns: the size of the bin which contains the tail_avg. Smaller bin size
    means more anomalous.
    """

    try:
        series = np.array([x[1] for x in timeseries])
        t = tail_avg(timeseries, debug, debug_path)
        h = np.histogram(series, bins=15)
        bins = h[1]
        for index, bin_size in enumerate(h[0]):
            if bin_size <= 20:
                # Is it in the first bin?
                if index == 0:
                    if t <= bins[0]:
                        return True
                # Is it in the current bin?
                elif t >= bins[index] and t < bins[index + 1]:
                        return True

        return False
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in histogram_bins - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None
