"""
Some algorithms from the original skyline implementation are commented out and
the best combination of algorithms for NAB is included below.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas



def tail_avg(timeseries):
  """
  This is a utility function used to calculate the average of the last three
  datapoints in the series as a measure, instead of just the last datapoint.
  It reduces noise, but it also reduces sensitivity and increases the delay
  to detection.
  """
  try:
    t = (timeseries[-1][1] + timeseries[-2][1] + timeseries[-3][1]) / 3
    return t
  except IndexError:
    return timeseries[-1][1]



def median_absolute_deviation(timeseries):
  """
  A timeseries is anomalous if the deviation of its latest datapoint with
  respect to the median is X times larger than the median of deviations.
  """

  series = pandas.Series([x[1] for x in timeseries])
  median = series.median()
  demedianed = np.abs(series - median)
  median_deviation = demedianed.median()

  # The test statistic is infinite when the median is zero,
  # so it becomes super sensitive. We play it safe and skip when this happens.
  if median_deviation == 0:
    return False

  test_statistic = demedianed.iloc[-1] / median_deviation

  # Completely arbitary...triggers if the median deviation is
  # 6 times bigger than the median
  if test_statistic > 6:
    return True
  else:
    return False



# The method below is excluded because it is computationally inefficient
# def grubbs(timeseries):
#     """
#     A timeseries is anomalous if the Z score is greater than the Grubb's
# score.
#     """

#     series = np.array([x[1] for x in timeseries])
#     stdDev = np.std(series)
#     mean = np.mean(series)
#     tail_average = tail_avg(timeseries)
#     z_score = (tail_average - mean) / stdDev
#     len_series = len(series)
#     threshold = scipy.stats.t.isf(.05 / (2 * len_series), len_series - 2)
#     threshold_squared = threshold * threshold
#     grubbs_score = ((len_series - 1) / np.sqrt(len_series)) * np.sqrt(
#   threshold_squared / (len_series - 2 + threshold_squared))

#     return z_score > grubbs_score


def first_hour_average(timeseries):
  """
  Calcuate the simple average over one hour, one day ago.
  A timeseries is anomalous if the average of the last three datapoints
  are outside of three standard deviations of this value.
  """
  day = timedelta(days=1)
  hour = timedelta(hours=1)
  last_hour_threshold = timeseries[-1][0] - (day - hour)
  startTime = last_hour_threshold - hour
  series = pandas.Series([x[1] for x in timeseries
                          if x[0] >= startTime
                          and x[0] < last_hour_threshold])
  mean = (series).mean()
  stdDev = (series).std()
  t = tail_avg(timeseries)

  return abs(t - mean) > 3 * stdDev



def stddev_from_average(timeseries):
  """
  A timeseries is anomalous if the absolute value of the average of the latest
  three datapoint minus the moving average is greater than three standard
  deviations of the average. This does not exponentially weight the MA and so
  is better for detecting anomalies with respect to the entire series.
  """
  series = pandas.Series([x[1] for x in timeseries])
  mean = series.mean()
  stdDev = series.std()
  t = tail_avg(timeseries)

  return abs(t - mean) > 3 * stdDev



def stddev_from_moving_average(timeseries):
  """
  A timeseries is anomalous if the absolute value of the average of the latest
  three datapoint minus the moving average is greater than three standard
  deviations of the moving average. This is better for finding anomalies with
  respect to the short term trends.
  """
  series = pandas.Series([x[1] for x in timeseries])
  expAverage = series.ewm(ignore_na=False, min_periods=0, adjust=True, com=50).mean()
  stdDev = series.ewm(ignore_na=False, min_periods=0, adjust=True, com=50).std(bias=False)

  return abs(series.iloc[-1] - expAverage.iloc[-1]) > 3 * stdDev.iloc[-1]



def mean_subtraction_cumulation(timeseries):
  """
  A timeseries is anomalous if the value of the next datapoint in the
  series is farther than three standard deviations out in cumulative terms
  after subtracting the mean from each data point.
  """

  series = pandas.Series([x[1] if x[1] else 0 for x in timeseries])
  series = series - series[0:len(series) - 1].mean()
  stdDev = series[0:len(series) - 1].std()

  return abs(series.iloc[-1]) > 3 * stdDev



def least_squares(timeseries):
  """
  A timeseries is anomalous if the average of the last three datapoints
  on a projected least squares model is greater than three sigma.
  """

  x = np.array(
    [(t[0] - datetime(1970, 1, 1)).total_seconds() for t in timeseries])
  y = np.array([t[1] for t in timeseries])
  A = np.vstack([x, np.ones(len(x))]).T
  results = np.linalg.lstsq(A, y)
  residual = results[1]
  m, c = np.linalg.lstsq(A, y)[0]
  errors = []
  for i, value in enumerate(y):
    projected = m * x[i] + c
    error = value - projected
    errors.append(error)

  if len(errors) < 3:
    return False

  std_dev = np.std(errors)
  t = (errors[-1] + errors[-2] + errors[-3]) / 3

  return abs(t) > std_dev * 3 and round(std_dev) != 0 and round(t) != 0



def histogram_bins(timeseries):
  """
  A timeseries is anomalous if the average of the last three datapoints falls
  into a histogram bin with less than 20 other datapoints (you'll need to tweak
  that number depending on your data)

  Returns: the size of the bin which contains the tail_avg. Smaller bin size
  means more anomalous.
  """

  series = np.array([x[1] for x in timeseries])
  t = tail_avg(timeseries)
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


# The method below is excluded because it is computationally inefficient
# def ks_test(timeseries):
#     """
#     A timeseries is anomalous if 2 sample Kolmogorov-Smirnov test indicates
#     that data distribution for last 10 minutes is different from last hour.
#     It produces false positives on non-stationary series so Augmented
#     Dickey-Fuller test applied to check for stationarity.
#     """

#     hour_ago = time() - 3600
#     ten_minutes_ago = time() - 600
#     reference = scipy.array(
  # [x[1] for x in timeseries if x[0] >= hour_ago and x[0] < ten_minutes_ago])
#     probe = scipy.array([x[1] for x in timeseries if x[0] >= ten_minutes_ago])

#     if reference.size < 20 or probe.size < 20:
#         return False

#     ks_d, ks_p_value = scipy.stats.ks_2samp(reference, probe)

#     if ks_p_value < 0.05 and ks_d > 0.5:
#         adf = sm.tsa.stattools.adfuller(reference, 10)
#         if adf[1] < 0.05:
#             return True

#     return False

# The method below is excluded because it has no effect on the final skyline
# scores for NAB
# def is_anomalously_anomalous(metric_name, ensemble, datapoint):
#     """
#     This method runs a meta-analysis on the metric to determine whether the
#     metric has a past history of triggering.
# TODO: weight intervals based on datapoint
#     """
#     # We want the datapoint to avoid triggering twice on the same data
#     new_trigger = [time(), datapoint]

#     # Get the old history
#     raw_trigger_history = redis_conn.get("trigger_history." + metric_name)
#     if not raw_trigger_history:
#         redis_conn.set("trigger_history." + metric_name, packb(
  # [(time(), datapoint)]))
#         return True

#     trigger_history = unpackb(raw_trigger_history)

#     # Are we (probably) triggering on the same data?
#     if (new_trigger[1] == trigger_history[-1][1] and
#             new_trigger[0] - trigger_history[-1][0] <= 300):
#                 return False

#     # Update the history
#     trigger_history.append(new_trigger)
#     redis_conn.set("trigger_history." + metric_name, packb(trigger_history))

#     # Should we surface the anomaly?
#     trigger_times = [x[0] for x in trigger_history]
#     intervals = [
#         trigger_times[i + 1] - trigger_times[i]
#         for i, v in enumerate(trigger_times)
#         if (i + 1) < len(trigger_times)
#     ]

#     series = pandas.Series(intervals)
#     mean = series.mean()
#     stdDev = series.std()

#     return abs(intervals[-1] - mean) > 3 * stdDev


# def run_selected_algorithm(timeseries, metric_name):
#   """
#   Filter timeseries and run selected algorithm.
#   """
#   # Get rid of short series
#   if len(timeseries) < MIN_TOLERABLE_LENGTH:
#     raise TooShort()

#   # Get rid of stale series
#   if time() - timeseries[-1][0] > STALE_PERIOD:
#     raise Stale()

#   # Get rid of boring series
#   if len(
  # set(
    # item[1] for item in timeseries[
    # -MAX_TOLERABLE_BOREDOM:])) == BOREDOM_SET_SIZE:
#     raise Boring()

#   try:
#     ensemble = [globals()[algorithm](timeseries) for algorithm in ALGORITHMS]
#     threshold = len(ensemble) - CONSENSUS
#     if ensemble.count(False) <= threshold:
#       if ENABLE_SECOND_ORDER:
#         if is_anomalously_anomalous(metric_name, ensemble, timeseries[-1][1]):
#           return True, ensemble, timeseries[-1][1]
#       else:
#           return True, ensemble, timeseries[-1][1]

#     return False, ensemble, timeseries[-1][1]
#   except:
#     logging.error("Algorithm error: " + traceback.format_exc())
#     return False, [], 1