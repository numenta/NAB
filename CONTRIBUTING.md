NAB is intended for the research community and we encourage your contributions and feedback!

Before your [pull requests](https://help.github.com/articles/using-pull-requests) can be reviewed by our team, you'll need to sign our [Contributor License](https://numenta.com/contributor-license).


#### Data
We welcome data you're willing to contribute. Specifically we're looking for data meeting the following criteria:
* real-world time-series data
* \>1000 records
* labeled anomalies

#### Anomaly detection algorithms
For us to consider adding your algorithm to the NAB repo it must meet the following criteria:
* open-source
* work with streaming data (i.e. process data in real-time)
* we must be able to fully-replicate your results

For an algorithm to be used in practice it must run online as data is streaming in, and not in batch. It is necessary the algorithms are computationally efficient to process streaming data, i.e O(N). The following algorithms have been tested on NAB and do not meet this criteria:
- [Lytics Anomalyzer](https://github.com/lytics/anomalyzer)
  - Runs in O(N^2) because for each subsequent record the model retrains over all previous records.
  - The author recommended using the detector within a moving window (250 records) to speed up the algorithm, yielding the following results: 4.42 on the standard profile, 2.39 for rewarding low FP, and 8.58 for rewarding low FN. However this still ran quite slow; e.g. running Anomalyzer on "realKnownCause/machine_temperature_system_failure.csv" took 52m0s, but only 4m39s for the HTM detector.

We investigated some popular open-source algorithms to add to NAB, and have found the following unsuitable for streaming/online anomaly detection:
- [Yahoo EGADS](https://github.com/yahoo/egads) separates time series modeling from anomaly detection. To detect anomalies EGADS compares the prediction error to a threshold, and it determines this threshold by scanning the whole data file. It may be possible to use a small part of EGADS to output a set of anomaly scores by simply outputting the prediction error, but this calls for a hardcoded threshold and is a significant departure from the algorithm.
- [Netflix's "Robust Anomaly Detection" (RAD)](https://github.com/Netflix/Surus) uses Robust Principal Component Analysis (RPCA), which is not inherently aware of time. RAD applies RPCA to time series by chunking the data according to a seasonality that you specify, thus creating "time dimensions". The algorithm scans an entire time series, and then decides where the anomalies occurred.
- [LinkedIn's luminol](https://github.com/linkedin/luminol) is a general time-series analysis toolkit, with several algorithms for anomaly detection. However, these algorithms run in batch, not streaming; they process an entire time-series and return the anomalous time windows after the fact.

#### Comments/suggestions
Want to suggest some changes to the NAB codebase? Submit an [issue](https://github.com/numenta/NAB/issues/new) and/or pull request and we'll take a look.
