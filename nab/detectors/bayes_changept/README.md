# Bayesian Online Changepoint Detection

Implementation of the online Bayesian changepoint detection algorithm as described by [R. Adams and D. MacKay in "Bayesian Online Changepoint Detection"](https://hips.seas.harvard.edu/files/adams-changepoint-tr-2007.pdf).

The algorithm implemented here is a port from the [MATLAB code posted by R. Adams](http://hips.seas.harvard.edu/content/bayesian-online-changepoint-detection). The algorithm computes, for each record at step x in a data stream, the probability that the current record is part of a stream of length n for all n <= x. For a given record, if the maximimum of all the probabilities corresponds to a stream length of zero, the record represents a changepoint in the data stream. These probabilities are used to calculate anomaly scores for NAB results.
