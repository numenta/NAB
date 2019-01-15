"""
All algorithms from the original skyline implementation are included below.
"""

import numpy as np
import scipy
from scipy.stats import t as scipy_stats_t
import statsmodels.api as sm
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


# The method below is excluded because it is computationally inefficient
# And included again for earthgecko_skyline
def grubbs(timeseries, debug, debug_path):
    """
    A timeseries is anomalous if the Z score is greater than the Grubb's score.
    """

    try:
        series = scipy.array([x[1] for x in timeseries])
        stdDev = scipy.std(series)
        if stdDev == 0:
            return False

        mean = np.mean(series)
        tail_average = tail_avg(timeseries, debug, debug_path)
        z_score = (tail_average - mean) / stdDev
        len_series = len(series)
        threshold = scipy_stats_t.isf(.05 / (2 * len_series), len_series - 2)
        threshold_squared = threshold * threshold
        grubbs_score = ((len_series - 1) / np.sqrt(len_series)) * np.sqrt(threshold_squared / (len_series - 2 + threshold_squared))

        return z_score > grubbs_score
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in grubbs - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None


# The method below was excluded in NAB skyline_detector because it is computationally inefficient
# It was reinitroduced in earthgecko_skyline detector
def ks_test(timeseries, debug, debug_path):
    """
    A timeseries is anomalous if 2 sample Kolmogorov-Smirnov test indicates
    that data distribution for last 10 minutes is different from last hour.
    It produces false positives on non-stationary series so Augmented
    Dickey-Fuller test applied to check for stationarity.
    """

    try:
        hour_ago = timeseries[-1][0] - 3600
        ten_minutes_ago = timeseries[-1][0] - 600
        reference = scipy.array([x[1] for x in timeseries if x[0] >= hour_ago and x[0] < ten_minutes_ago])
        probe = scipy.array([x[1] for x in timeseries if x[0] >= ten_minutes_ago])

        if reference.size < 20 or probe.size < 20:
            return False

        ks_d, ks_p_value = scipy.stats.ks_2samp(reference, probe)

        if ks_p_value < 0.05 and ks_d > 0.5:
            adf = sm.tsa.stattools.adfuller(reference, 10)
            if adf[1] < 0.05:
                return True

        return False
    except:
        if debug:
            trace = traceback.format_exc()
            errorline = 'error in ks_test - %s\n' % str(trace)
            with open(debug_path + '/nab.earthgecko_skyline.algorithm.errors.txt', 'a') as errorfile:
                errorfile.write(errorline)
        return None

    return False
