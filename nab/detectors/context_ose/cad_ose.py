# ----------------------------------------------------------------------
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

from functools import cmp_to_key
from nab.detectors.context_ose.context_operator import ContextOperator

class ContextualAnomalyDetectorOSE(object):

  """
  Contextual Anomaly Detector - Open Source Edition
  2016, Mikhail Smirnov   smirmik@gmail.com
  https://github.com/smirmik/CAD
  """

  def __init__( self,
                minValue,
                maxValue,
                baseThreshold = 0.75,
                restPeriod = 30,
                maxLeftSemiContextsLenght = 7,
                maxActiveNeuronsNum = 15,
                numNormValueBits = 3 ) :

    self.minValue = float(minValue)
    self.maxValue = float(maxValue)
    self.restPeriod = restPeriod
    self.baseThreshold = baseThreshold
    self.maxActNeurons = maxActiveNeuronsNum
    self.numNormValueBits = numNormValueBits

    self.maxBinValue = 2 ** self.numNormValueBits - 1.0
    self.fullValueRange = self.maxValue - self.minValue
    if self.fullValueRange == 0.0 :
      self.fullValueRange = self.maxBinValue
    self.minValueStep = self.fullValueRange / self.maxBinValue

    self.leftFactsGroup = tuple()

    self.contextOperator = ContextOperator( maxLeftSemiContextsLenght )

    self.potentialNewContexts = []

    self.aScoresHistory = [ 1.0 ]


  def step(self, inpFacts):

    currSensFacts = tuple(sorted(set(inpFacts)))

    uniqPotNewContexts = set()

    if len(self.leftFactsGroup) > 0 and len(currSensFacts) > 0 :
      potNewZeroLevelContext = tuple([self.leftFactsGroup,currSensFacts])
      uniqPotNewContexts.add(potNewZeroLevelContext)
      newContextFlag = self.contextOperator.getContextByFacts(
        [potNewZeroLevelContext],
        zerolevel = 1
      )
    else :
      newContextFlag = False

    leftCrossing = self.contextOperator.contextCrosser (
      leftOrRight = 1,
      factsList = currSensFacts,
      newContextFlag = newContextFlag
    )
    activeContexts, numSelContexts, potNewContexts = leftCrossing

    uniqPotNewContexts.update(potNewContexts)
    numUniqPotNewContext = len(uniqPotNewContexts)

    if numSelContexts > 0 :
      percentSelectedContextActive = len(activeContexts) / float(numSelContexts)
    else :
      percentSelectedContextActive = 0.0

    srtAContexts = sorted(activeContexts, key=lambda x: (x[1], x[2], x[3]))
    activeNeurons = [ cInf[0] for cInf in srtAContexts[-self.maxActNeurons:] ]

    currNeurFacts = set([ 2 ** 31 + fact for fact in activeNeurons ])

    leftFactsGroup = set()
    leftFactsGroup.update(currSensFacts, currNeurFacts)
    self.leftFactsGroup = tuple(sorted(leftFactsGroup))

    numNewCont  =  self.contextOperator.contextCrosser  (
      leftOrRight = 0,
      factsList = self.leftFactsGroup,
      potentialNewContexts = potNewContexts
    )

    numNewCont += 1 if newContextFlag else 0

    if newContextFlag and numUniqPotNewContext > 0 :
      percentAddedContextToUniqPotNew = numNewCont / float(numUniqPotNewContext)
    else :
      percentAddedContextToUniqPotNew = 0.0

    return  percentSelectedContextActive, percentAddedContextToUniqPotNew


  def getAnomalyScore(self,inputData):

    normInpVal = int((inputData["value"] - self.minValue) / self.minValueStep)
    binInpValue = bin(normInpVal).lstrip("0b").rjust(self.numNormValueBits,"0")

    outSens = []
    for sNum, currSymb in enumerate(reversed(binInpValue)) :
      outSens.append( sNum * 2 + ( 1 if currSymb == "1" else 0 ) )
    setOutSens = set(outSens)

    anomalyVal1, anomalyVal2 = self.step(setOutSens)
    currentAnomalyScore = (1.0 - anomalyVal1 + anomalyVal2) / 2.0

    if max(self.aScoresHistory[-int(self.restPeriod):]) < self.baseThreshold :
      returnedAnomalyScore = currentAnomalyScore
    else :
      returnedAnomalyScore = 0.0

    self.aScoresHistory.append(currentAnomalyScore)

    return returnedAnomalyScore
