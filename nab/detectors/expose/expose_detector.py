import numpy

from sklearn.kernel_approximation import RBFSampler

from nab.detectors.base import AnomalyDetector



class ExposeDetector(AnomalyDetector):

  """ This detector is an implementation of The EXPoSE (EXPected Similarity
  Estimation) algorithm as described in Markus Schneider, Wolfgang Ertel,
  Fabio Ramos, "Expected Similarity Estimation for Lage-Scale Batch and
  Streaming Anomaly Detection", arXiv 1601.06602 (2016).

  EXPoSE calculates the likelihood of a data point being normal by using
  the inner product of its feature map with kernel embedding of previous data
  points. This measures the similarity of a data point to previous points
  without assuming an underlying data distribution.

  There are three EXPoSE variants: incremental, windowing and decay. This
  implementation is based on EXPoSE with decay. All three variants have been
  tried on NAB but decay gives the best results.Parameters for this detector
  have been tuned to give the best performance.
  """

  def __init__(self, *args, **kwargs):
    super(ExposeDetector, self).__init__(*args, **kwargs)

    self.kernel = None
    self.previousExposeModel = []
    self.decay = 0.01
    self.timestep = 0


  def initialize(self):
    """Initializes RBFSampler for the detector"""
    self.kernel = RBFSampler(gamma=0.5,
                             n_components=20000,
                             random_state=290)


  def handleRecord(self, inputData):
    """ Returns a list [anomalyScore] calculated using a kernel based
    similarity method described in the comments below"""

    # Transform the input by approximating feature map of a Radial Basis
    # Function kernel using Random Kitchen Sinks approximation
    inputFeature = self.kernel.fit_transform(
      numpy.array([[inputData["value"]]]))

    # Compute expose model as a weighted sum of new data point's feature
    # map and previous data points' kernel embedding. Influence of older data
    # points declines with the decay factor.
    if self.timestep == 0:
      exposeModel = inputFeature
    else:
      exposeModel = ((self.decay * inputFeature) + (1 - self.decay) *
                     self.previousExposeModel)

    # Update previous expose model
    self.previousExposeModel = exposeModel

    # Compute anomaly score by calculating similarity of the new data point
    # with expose model. The similarity measure, calculated via inner
    # product, is the likelihood of data point being normal. Resulting
    # anomaly scores are in the range of -0.02 to 1.02.
    anomalyScore = numpy.asscalar(1 - numpy.inner(inputFeature, exposeModel))
    self.timestep += 1

    return [anomalyScore]
