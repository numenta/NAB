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

class ContextOperator(object):
  
  """
  Contextual Anomaly Detector - Open Source Edition
  2016, Mikhail Smirnov   smirmik@gmail.com
  https://github.com/smirmik/CAD
  """

  def __init__(self, maxLeftSemiContextsLenght):

    self.maxLeftSemiContextsLenght = maxLeftSemiContextsLenght

    self.factsDics = [{},{}]
    self.semiContextDics = [{},{}]
    self.semiContValLists = [[],[]]
    self.crossedSemiContextsLists = [[],[]]
    self.contextsValuesList = []

    self.newContextID = False


  def getContextByFacts (self, newContextsList, zerolevel = 0 ) :
    """
    The function which determines by the complete facts list whether the
    context is already saved to the memory. If the context is not found the
    function immediately creates such. To optimize speed and volume of the
    occupied memory the contexts are divided into semi-contexts as several
    contexts can contain the same facts set in its left and right parts.

    @param newContextsList:     list of potentially new contexts

    @param zerolevel:         flag indicating the context type in
                    transmitted list

    @return : depending on the type of  potentially new context transmitted as
          an input parameters the function returns either:
          a) flag indicating that the transmitted zero-level context is
          a new/existing one;
          or:
          b) number of the really new contexts that have been saved to the
          context memory.
    """


    numAddedContexts = 0

    for leftFacts, rightFacts in newContextsList :

      leftHash = leftFacts.__hash__()
      rightHash = rightFacts.__hash__()

      nextLeftSemiContextNumber = len(self.semiContextDics[0])
      leftSemiContextID = self.semiContextDics[0].setdefault(
        leftHash,
        nextLeftSemiContextNumber
      )
      if leftSemiContextID == nextLeftSemiContextNumber :
        leftSemiContVal = [[] , len(leftFacts), 0, {}]
        self.semiContValLists[0].append(leftSemiContVal)
        for fact in leftFacts :
          semiContextList = self.factsDics[0].setdefault(fact, [])
          semiContextList.append(leftSemiContVal)

      nextRightSemiContextNumber = len(self.semiContextDics[1])
      rightSemiContextID = self.semiContextDics[1].setdefault(
        rightHash,
        nextRightSemiContextNumber
      )
      if  rightSemiContextID == nextRightSemiContextNumber :
        rightSemiContextValues = [[] , len(rightFacts), 0]
        self.semiContValLists[1].append(rightSemiContextValues)
        for fact in rightFacts :
          semiContextList = self.factsDics[1].setdefault(fact, [])
          semiContextList.append(rightSemiContextValues)

      nextFreeContextIDNumber = len(self.contextsValuesList)
      contextID = self.semiContValLists[0][leftSemiContextID][3].setdefault(
        rightSemiContextID,
        nextFreeContextIDNumber
      )

      if contextID == nextFreeContextIDNumber :
        numAddedContexts += 1
        contextValues = [0, zerolevel, leftHash, rightHash]

        self.contextsValuesList.append(contextValues)
        if zerolevel :
          self.newContextID = contextID
          return True
      else :
        contextValues = self.contextsValuesList[contextID]

        if zerolevel :
          contextValues[1] = 1
          return False


    return numAddedContexts


  def contextCrosser( self,
                      leftOrRight,
                      factsList,
                      newContextFlag = False,
                      potentialNewContexts = None):

    if leftOrRight == 0 :
      if len(potentialNewContexts) > 0 :
        numNewContexts = self.getContextByFacts (potentialNewContexts)
      else :
        numNewContexts = 0

    for semiContextValues in self.crossedSemiContextsLists[leftOrRight] :
      semiContextValues[0] = []
      semiContextValues[2] = 0

    for fact in factsList :
      for semiContextValues in self.factsDics[leftOrRight].get(fact, []) :
        semiContextValues[0].append(fact)

    newCrossedValues = []

    for semiContextValues in self.semiContValLists[leftOrRight] :
      lenSemiContextValues0 = len(semiContextValues[0])
      semiContextValues[2] = lenSemiContextValues0
      if lenSemiContextValues0 > 0 :
        newCrossedValues.append(semiContextValues)

    self.crossedSemiContextsLists[leftOrRight] = newCrossedValues

    if  leftOrRight :
      return self.updateContextsAndGetActive(newContextFlag)

    else :
      return numNewContexts


  def updateContextsAndGetActive(self, newContextFlag):
    """
    This function reviews the list of previously selected left semi-contexts,
    creates the list of potentially new contexts resulted from intersection
    between zero-level contexts, determines the contexts that coincide with
    the input data and require activation.

    @param newContextFlag:     flag indicating that a new zero-level
                    context is not recorded at the current
                    step, which means that all contexts
                    already exist and there is no need to
                    create new ones.

    @return activeContexts:     list of identifiers of the contexts which
                    completely coincide with the input stream,
                    should be considered active and be
                    recorded to the input stream of "neurons"

    @return potentialNewContextsLists:  list of contexts based on intersection
                    between the left and the right zero-level
                    semi-contexts, which are potentially new
                    contexts requiring saving to the context
                    memory
    """

    activeContexts = []
    numSelectedContext = 0

    potentialNewContexts = []

    for leftSemiContVal in self.crossedSemiContextsLists[0]:

      for rightSemiContextID, contextID in leftSemiContVal[3].items():

        if self.newContextID != contextID :

          contextValues = self.contextsValuesList[contextID]
          rightSemiContVal = self.semiContValLists[1][rightSemiContextID]
          rightSemConVal0,  rightSemConVal1, rightSemConVal2 = rightSemiContVal

          if leftSemiContVal[1] == leftSemiContVal[2] :

            numSelectedContext += 1

            if rightSemConVal2 > 0 :

              if rightSemConVal1 == rightSemConVal2 :
                contextValues[0] += 1
                activeContexts.append([ contextID,
                                        contextValues[0],
                                        contextValues[2],
                                        contextValues[3]
                                      ])

              elif contextValues[1] and newContextFlag :
                if leftSemiContVal[2] <= self.maxLeftSemiContextsLenght :
                  leftFacts = tuple(leftSemiContVal[0])
                  rightFacts = tuple(rightSemConVal0)
                  potentialNewContexts.append(tuple([leftFacts, rightFacts]))

          elif contextValues[1] and newContextFlag and rightSemConVal2 > 0 :
            if leftSemiContVal[2] <= self.maxLeftSemiContextsLenght :
              leftFacts = tuple(leftSemiContVal[0])
              rightFacts = tuple(rightSemConVal0)
              potentialNewContexts.append(tuple([leftFacts, rightFacts]))

    self.newContextID = False

    return activeContexts, numSelectedContext, potentialNewContexts
