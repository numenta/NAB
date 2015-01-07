# ----------------------------------------------------------------------
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

from nab.scorer import scoreCorpus



def optimizeThreshold(args):
  """Optimize the threshold for a given combination of detector and profile.

  @param args       (tuple)   Arguments necessary for the objective function.

  @param tolerance  (float)   Number used to determine when optimization has
                              converged to a sufficiently good score.

  @return (dict) Contains:
        "threshold" (float)   Threshold that returns the largest score from the
                              Objective function.

        "score"     (float)   The score from the objective function given the
                              threshold.
  """
  result = twiddle(
    objFunction=objectiveFunction,
    args=args,
    initialGuess=0.5,
    tolerance=.00001)

  answer = {}

  answer['threshold'] = result['parameter']

  answer['score'] = result['score']

  return answer


def twiddle(objFunction, args, initialGuess=0.5, tolerance=0.00001, domain=(float("-inf"), float("inf"))):
  """Optimize a single parameter given an objective function.

  This is a local hill-climbing algorithm. Here is a simple description of it:
  https://www.youtube.com/watch?v=2uQ2BSzDvXs

  @param args       (tuple)   Arguments necessary for the objective function.

  @param tolerance  (float)   Number used to determine when optimization has
                              converged to a sufficiently good score. Should be
                              very low to yield precise likelihood values.

  @param objFunction(function)Objective Function used to quantify how good a
                              particular parameter choice is.

  @param init       (float)   Initial value of the parameter.
  
  @param domain     (tuple)   Domain of parameter values, as (min, max).

  @return (dict) Contains:
        "parameter" (float)   Threshold that returns the largest score from the
                              Objective function.

        "score"     (float)   The score from the objective function given the
                              threshold.
  """
  pastCalls = {}
  x = initialGuess
  delta = 0.1
  bestScore = objFunction(x, args)

  pastCalls[x] = bestScore

  while delta > tolerance:
  
    # Keep x within bounds
    if x+delta > domain[1]:
      delta = abs(domain[1] - x) / 2
    x += delta

    if x not in pastCalls:
      score = objFunction(x, args)
      pastCalls[x] = score

    score = pastCalls[x]

    if score > bestScore:
      bestScore = score
      delta *= 2

    else:
      # Keep x within bounds
      if x-delta < domain[0]:
        delta = abs(domain[0] - x) / 2
      x -= 2*delta

      if x not in pastCalls:
        score = objFunction(x, args)
        pastCalls[x] = score

      score = pastCalls[x]

      if score > bestScore:
        bestScore = score
        delta *= 2
      else:
        x += delta
        delta *= 0.5

    print "Parameter:", x
    print "Best score:", bestScore
    print "Step size:", delta
    print

  return {"parameter": x,
          "score": bestScore}


def objectiveFunction(threshold, args):
  """Objective function that scores the corpus given a specific threshold.

  @param threshold  (float)   Threshold value to convert an anomaly score value
                              to a detection.

  @param args       (tuple)   Arguments necessary to call scoreHelper.

  @return score     (float)   Score of corpus.
  """
  if not 0 <= threshold <= 1:
    return float("-inf")

  resultsDataFrame = scoreCorpus(threshold, args)

  score = float(resultsDataFrame["Score"].iloc[-1])

  return score
