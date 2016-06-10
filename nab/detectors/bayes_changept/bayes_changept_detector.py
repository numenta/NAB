"""
Anomaly detection algorithm that implements Bayesian changepoint detection, as
described in
  Ryan P. Adams, David J.C. MacKay, Bayesian Online Changepoint Detection,
arXiv 0710.3742 (2007).

For the author's implementation (in MATLAB) please see
http://hips.seas.harvard.edu/content/bayesian-online-changepoint-detection

It has been modified from the author's code to run online: rather than
initializing a run-length matrix with the size of the dataset, we use an array
that recursively overwrites old data (no longer needed by the algorithm).
"""
from functools import partial
import numpy
from scipy import stats

from nab.detectors.base import AnomalyDetector



class BayesChangePtDetector(AnomalyDetector):

  def __init__(self, *args, **kwargs):

    super(BayesChangePtDetector, self).__init__(*args, **kwargs)

    # Setup the matrix that will hold our beliefs about the current
    # run lengths. We'll initialize it all to zero at first. For efficiency
    # we preallocate a data structure to hold only the info we need to detect
    # change points: columns for the current timestep t and t+1, and a
    # sufficient number of rows (where each row represents probabilites of a
    # run of that length).
    self.maxRunLength = 500
    self.runLengthProbs = numpy.zeros((self.maxRunLength + 2, 2))
    # Time t=0 is a boundary condition, where we know the run length is 0.
    self.runLengthProbs[0, 0] = 1.0

    # Init variables for state.
    self.timestep = 0
    self.previousMaxRun = 1

    # Define algorithm's helpers.
    self.observationLikelihoood = StudentT(alpha=0.1,
                                           beta=0.001,
                                           kappa=1.0,
                                           mu=0.0)
    self.hazardFunction = partial(constantHazard, 250)


  def handleRecord(self, inputData):
    """
    Returns a list [anomalyScore]. Algorithm details are in the comments below.
    """
    # To accomodate this next timestep, shift the columns of the run length
    # probabilities matrix.
    if self.timestep > 0:
      for row in self.runLengthProbs:
        row[0] = row[1]
        row[1] = 0.0

    x = inputData["value"]

    # Evaluate the predictive distribution for the new datum under each of
    # the parameters. This is standard Bayesian inference.
    predProbs = self.observationLikelihoood.pdf(x)

    # Evaluate the hazard function for this interval
    hazard = self.hazardFunction(numpy.array(range(self.timestep+1)))

    # We only keep use the calculate probabilites up to maxRunLength.
    if self.timestep < self.maxRunLength:
      timestep = self.timestep
    else:
      timestep = self.maxRunLength

    # Evaluate the growth probabilities -- shift the probabilities down and to
    # the right, scaled by the hazard function and the predictive probabilities.
    self.runLengthProbs[1:timestep+2, 1] = (
        self.runLengthProbs[:timestep+1, 0] *
        predProbs[:self.maxRunLength+1] *
        (1-hazard)[:self.maxRunLength+1]
    )

    # Evaluate the probability that there *was* a changepoint and we're
    # accumulating the probability mass back down at run length = 0.
    self.runLengthProbs[0, 1] = numpy.sum(
        self.runLengthProbs[:timestep+1, 0] *
        predProbs[:self.maxRunLength+1] *
        hazard[:self.maxRunLength+1]
    )

    # Renormalize the run length probabilities for improved numerical stability.
    self.runLengthProbs[:, 1] = (self.runLengthProbs[:, 1] /
                                 self.runLengthProbs[:, 1].sum())

    # Update the parameter sets for each possible run length.
    self.observationLikelihoood.updateTheta(x)

    # Get the current run length with the highest probability.
    maxRecursiveRunLength = self.runLengthProbs[:, 1].argmax()

    # To calculate anomaly scores from run length probabilites we have several
    # options, implemented below:
    #   1. If the max probability for any run length is the run length of 0, we
    #   have a changepoint, thus anomaly score = 1.0.
    #   2. The anomaly score is the probability of run length 0.
    #   3. Compute a score by assuming a change in sequence from a previously
    #   long run is more anomalous than a change from a short run.
    # Option 3 results in the best anomaly detections (by far):
    if maxRecursiveRunLength < self.previousMaxRun:
      anomalyScore = 1 - (float(maxRecursiveRunLength) / self.previousMaxRun)
    else:
      anomalyScore = 0.0

    # Update state vars.
    self.timestep += 1
    self.previousMaxRun = maxRecursiveRunLength

    return [anomalyScore]



def constantHazard(lam, r):
  return 1/float(lam) * numpy.ones(r.shape)
  # return numpy.ones(r.shape)/float(lam)



class StudentT:

  def __init__(self, alpha, beta, kappa, mu):
    self.alpha0 = self.alpha = numpy.array([alpha])
    self.beta0 = self.beta = numpy.array([beta])
    self.kappa0 = self.kappa = numpy.array([kappa])
    self.mu0 = self.mu = numpy.array([mu])


  def pdf(self, data):
    return stats.t.pdf(x=data,
                       df=2*self.alpha,
                       loc=self.mu,
                       scale=numpy.sqrt( (self.beta * (self.kappa+1)) /
                                         (self.alpha * self.kappa) )
                      )


  def updateTheta(self, data):
    muT0 = numpy.concatenate(
      (self.mu0, (self.kappa * self.mu + data) / (self.kappa + 1)))
    kappaT0 = numpy.concatenate((self.kappa0, self.kappa + 1.))
    alphaT0 = numpy.concatenate((self.alpha0, self.alpha + 0.5))
    betaT0 = numpy.concatenate((self.beta0, self.beta + (self.kappa * (data -
        self.mu)**2) / (2. * (self.kappa + 1.))))

    self.mu = muT0
    self.kappa = kappaT0
    self.alpha = alphaT0
    self.beta = betaT0
