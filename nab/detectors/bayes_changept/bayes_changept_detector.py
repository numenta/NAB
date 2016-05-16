"""
Anomaly detection algorithm that implements Bayesian changepoint detection, as
described in
  Ryan P. Adams, David J.C. MacKay, Bayesian Online Changepoint Detection,
arXiv 0710.3742 (2007).

For the author's implementation (in MATLAB) please see
http://hips.seas.harvard.edu/content/bayesian-online-changepoint-detection
"""
from functools import partial
import numpy
from scipy import stats

from nab.detectors.base import AnomalyDetector



class BayesChangePtDetector(AnomalyDetector):

  def __init__(self, *args, **kwargs):

    # Init the detector base
    super(BayesChangePtDetector, self).__init__(*args, **kwargs)

    datasetLength = len(self.dataSet.data)
    self.timestep = 0
    # Setup the matrix that will hold our beliefs about the current
    # run lengths. We'll initialize it all to zero at first. Obviously
    # we're assuming here that we know how long we're going to do the
    # inference.
    self.R = numpy.zeros((datasetLength + 1, datasetLength + 1))  ## TODO: switch to streaming
    self.stream = False
    self.rStream = [[]]
    # Time t=0 is a boundary condition, where we know the run length is 0.
    self.R[0, 0] = 1.0
    self.rStream[0].append(1.0)


    self.observationLikelihoood = StudentT(alpha=0.1,
                                           beta=0.001,
                                           kappa=1.0,
                                           mu=0.0)

    self.hazardFunction = partial(constantHazard, 250)


  def handleRecord(self, inputData):
    """
    We calculate the probability the data at this timestep represents a sequence
    length of 0 -- i.e. the probability of the current timestep to be a
    changepoint.

    Returns a list [anomalyScore].
    """
    # Add a column and a row to the run lengths dataframe to accomodate this
    # record.
    if self.stream:
      self.rStream.append([0.0]*len(self.rStream[0])) # add a row of zeros
      for row in self.rStream:  ## Add here or later with actual values??
        row.append(0.0) # add a column

    x = inputData["value"]

    # Evaluate the predictive distribution for the new datum under each of
    # the parameters. This is the standard thing from Bayesian inference.
    predProbs = self.observationLikelihoood.pdf(x)

    # Evaluate the hazard function for this interval
    hazard = self.hazardFunction(numpy.array(range(self.timestep+1)))

    # Evaluate the growth probabilities -- shift the probabilities down and to
    # the right, scaled by the hazard function and the predictive probabilities.
    if self.stream:
      for i in xrange(self.timestep+1):
        growthProb = self.rStream[i][self.timestep] * predProbs[i] * (1-hazard)[i]
        self.rStream[i+1][self.timestep+1] = growthProb
    self.R[1:self.timestep+2, self.timestep+1] = self.R[0:self.timestep+1, self.timestep] * predProbs * (1-hazard)

    ## validation stream/batch
    # import pdb; pdb.set_trace()
    # for i,row in enumerate(self.rStream):
    #   for j, val in enumerate(row):
    #     print val
    #     print self.R[i,j]
    #     # assert(val==self.R[i,j])


    # Evaluate the probability that there *was* a changepoint and we're
    # accumulating the mass back down at r = 0.
    if self.stream:
      newProb = 0.0
      for i in xrange(self.timestep+1):
        newProb += self.rStream[i][self.timestep] * predProbs[i] * hazard[i]
      self.rStream[0][self.timestep+1] = newProb
    prob = numpy.sum( self.R[0:self.timestep+1, self.timestep] * predProbs * hazard)
    self.R[0, self.timestep+1] = prob

    # Renormalize the run length probabilities for improved numerical stability.
    if self.stream:
      thisColumn = [row[self.timestep+1] for row in self.rStream]
      for i in xrange(len(self.rStream)):
        self.rStream[i][self.timestep+1] = thisColumn[i] / sum(thisColumn)
    self.R[:, self.timestep+1] = self.R[:, self.timestep+1] / numpy.sum(self.R[:, self.timestep+1])

    # Update the parameter sets for each possible run length.
    self.observationLikelihoood.updateTheta(x)

    # Whenever the max probability is associated w/ run length 1 we have a
    # change point. For anomaly detection we have several options, implemented
    # below:
    #   1. If the max probability for any run length is the run length of 1, we
    #   have a changepoint, thus anomaly score = 1.0.
    #   2. The anomaly score is the probability of run length 1.
    #   3. Misc. (see below)
    if self.stream:
      maxP = 0.0
      maxRecursiveRunLength = self.timestep+1
      for i, row in enumerate(self.rStream):
        if row[self.timestep+1] > maxP:
          maxP = row[self.timestep+1]
          maxRecursiveRunLength = i
    maxRecursiveRunLength = self.R[:, self.timestep+1].argmax()
    previousMax = self.R[:, self.timestep].argmax()

    # assert(maxRecursiveRunLength == maxRecursiveRunLength2)
    # print maxRecursiveRunLength, maxRecursiveRunLength2
    # print self.R[maxRecursiveRunLength, self.timestep+1], self.rStream[maxRecursiveRunLength2][self.timestep+1]
    # print self.timestep, maxRecursiveRunLength, self.R[maxRecursiveRunLength, self.timestep+1], x

    # Variations of option 1:
    #
    #   a. This is the most intuitive use of change point anomaly detection --> very negative scores (no optimizer)
    # rBuffer = 2
    # if maxRecursiveRunLength < rBuffer:
    #   anomalyScore = 1.0
    # else:
    #   anomalyScore = 0.0
    #   b. Use the run length to calc an anomaly score:
    # anomalyScore = 1 / float(maxRecursiveRunLength)

    # Variations of option 2:
    #
    #   a. Use the probability: --> 0s b/c best not to detect anomalies
    # anomalyScore = self.R[maxRecursiveRunLength, self.timestep+1]
    #
    #   b. Use the probability w/in some buffer:
    # rBuffer = 5  # large buffer helps mitigate FPs from spiky data? (5, 10, 20--> 0s)
    # if maxRecursiveRunLength < rBuffer:
    #   anomalyScore = self.R[maxRecursiveRunLength, self.timestep+1]
    # else:
    #   anomalyScore = 0.0

    # Assuming a change in sequence from a previously long run is more anomalous
    # than a change from a short run; helps combat FPs in spiky data streams.
    if maxRecursiveRunLength < previousMax:
      anomalyScore = 1 - (float(maxRecursiveRunLength) / previousMax)
    else:
      anomalyScore = 0.0

    self.timestep += 1

    return [anomalyScore]



def constantHazard(lam, r):
  return 1/float(lam) * numpy.ones(r.shape)
  # return numpy.ones(r.shape)/float(lam)  # this one's cleaner



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
                       scale=numpy.sqrt(self.beta * (self.kappa+1) / (self.alpha * self.kappa)))


  def updateTheta(self, data):
    muT0 = numpy.concatenate((self.mu0, (self.kappa * self.mu + data) / (self.kappa + 1)))
    kappaT0 = numpy.concatenate((self.kappa0, self.kappa + 1.))
    alphaT0 = numpy.concatenate((self.alpha0, self.alpha + 0.5))
    betaT0 = numpy.concatenate((self.beta0, self.beta + (self.kappa * (data -
        self.mu)**2) / (2. * (self.kappa + 1.))))

    self.mu = muT0
    self.kappa = kappaT0
    self.alpha = alphaT0
    self.beta = betaT0
