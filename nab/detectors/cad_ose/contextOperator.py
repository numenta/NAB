# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Contextual Anomaly Detector - Open Source Edition
# Copyright (C) 2016, Mikhail Smirnov   smirmik@gmail.com
# https://github.com/smirmik/CAD
#
# This program is free software: you can redistribute it and/or modify it under
# the terms  of  the  GNU Affero Public License version 3  as  published by the
# Free Software Foundation.
#
# This program is distributed  in  the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero Public License for more details.
#
# You should have received a copy of the  GNU Affero Public License  along with
# this program.  If not, see http://www.gnu.org/licenses.
#
# ------------------------------------------------------------------------------

class ContextOperator():


    def __init__(self, maxLeftSemiContextsLenght):

        self.maxLeftSemiContextsLenght = maxLeftSemiContextsLenght

        self.factsDics = [{},{}]
        self.semiContextDics = [{},{}]
        self.semiContextValuesLists = [[],[]]
        self.crossedSemiContextsLists = [[],[]]
        self.contextsValuesList = []

        self.newContextID = False


    def getContextByFacts (self, newContextsList, zerolevel = 0 ) :
        """
        The function which determines by the complete facts list whether the context
        is already saved to the memory. If the context is not found the function
        immediately creates such. To optimize speed and volume of the occupied memory
        the contexts are divided into semi-contexts as several contexts can contain
        the same facts set in its left and right parts.
         
        @param newContextsList:         list of potentially new contexts
        
        @param zerolevel:               flag indicating the context type in
                                        transmitted list
                                          
        @return :   depending on the type of  potentially new context transmitted as
                    an input parameters the function returns either:
                    а) flag indicating that the transmitted zero-level context is
                    a new/existing one;
                    or:
                    b) number of the really new contexts that have been saved to the
                    context memory.

        
        Функция, которая по полному списку фактов определяет существует ли уже в памяти
        данный контекст и в случае, если такого контекста нет - сразу создаёт его.
        Для оптимизации быстродействия и объема занимаемой оперативной памяти контексты
        разделены на полуконтексты, в связи с тем, что сразу несколько контекстов могут
        содержать одинаковый набор фактов в левой или правой части. 

        @param newContextsList:         список потенциально новых контекстов

        @param zerolevel:               флаг, указывающий на то, какой тип контекстов
                                        в передаваемом списке

        @return :   в зависимости от того, какой тип потенциально новых контекстов был
                    передан в качестве входных параметров, функция возвращает либо:
                    а) флаг, указывающий на то, что переданный контекст нулевого
                    уровня является новым/существующим, 
                    либо:
                    б) количество контекстов, которые действительно оказались новыми
                    и были сохранены в памяти контекстов.   
        
        """


        numAddedContexts = 0
        
        for leftFacts, rightFacts in newContextsList :

            leftHash = leftFacts.__hash__()
            rightHash = rightFacts.__hash__()
                
            nextLeftSemiContextNumber = len(self.semiContextDics[0]) 
            leftSemiContextID = self.semiContextDics[0].setdefault(leftHash, nextLeftSemiContextNumber)
            if leftSemiContextID == nextLeftSemiContextNumber :
                leftSemiContextValues = [[] , len(leftFacts), 0, {}]
                self.semiContextValuesLists[0].append(leftSemiContextValues)
                for fact in leftFacts :
                    semiContextList = self.factsDics[0].setdefault(fact, [])
                    semiContextList.append(leftSemiContextValues)
                
            nextRightSemiContextNumber = len(self.semiContextDics[1])
            rightSemiContextID = self.semiContextDics[1].setdefault(rightHash, nextRightSemiContextNumber)
            if  rightSemiContextID == nextRightSemiContextNumber :
                rightSemiContextValues = [[] , len(rightFacts), 0]
                self.semiContextValuesLists[1].append(rightSemiContextValues)
                for fact in rightFacts :
                    semiContextList = self.factsDics[1].setdefault(fact, [])
                    semiContextList.append(rightSemiContextValues)
            
            nextFreeContextIDNumber = len(self.contextsValuesList) 
            contextID = self.semiContextValuesLists[0][leftSemiContextID][3].setdefault(rightSemiContextID, nextFreeContextIDNumber)
            
            if contextID == nextFreeContextIDNumber :
                numAddedContexts += 1
                contextValues = [0, 0, 0, rightFacts, zerolevel, leftHash, rightHash]

                self.contextsValuesList.append(contextValues)
                if zerolevel :
                    self.newContextID = contextID
                    return True 
            else :
                contextValues = self.contextsValuesList[contextID]

                if zerolevel :
                    contextValues[4] = 1
                    return False


        return numAddedContexts


    def contextCrosser(self, leftOrRight, factsList, newContextFlag = False, potentialNewContexts = []):

        if leftOrRight == 0 :
            if len(potentialNewContexts) > 0 :
                numNewContexts = self.getContextByFacts (potentialNewContexts)
            else :
                numNewContexts = 0
            maxPredWeight = 0.0
            newPredictions = set()
            predictionContexts = []
            
        for semiContextValues in self.crossedSemiContextsLists[leftOrRight] :
            semiContextValues[0] = []
            semiContextValues[2] = 0

        for fact in factsList :
            for semiContextValues in self.factsDics[leftOrRight].get(fact, []) :
                semiContextValues[0].append(fact)
           
        newCrossedValues = []

        for semiContextValues in self.semiContextValuesLists[leftOrRight] :
            lenSemiContextValues0 = len(semiContextValues[0])
            semiContextValues[2] = lenSemiContextValues0
            if lenSemiContextValues0 > 0 :
                newCrossedValues.append(semiContextValues)
                if leftOrRight == 0 and semiContextValues[1] == lenSemiContextValues0 :
                    for contextID in semiContextValues[3].itervalues():
                        contextValues = self.contextsValuesList[contextID]
                        
                        currPredWeight = contextValues[1] / float(contextValues[0]) if contextValues[0] > 0 else 0.0

                        if currPredWeight >  maxPredWeight :
                            maxPredWeight = currPredWeight
                            predictionContexts = [contextValues]
                            
                        elif currPredWeight ==  maxPredWeight :
                            predictionContexts.append(contextValues)

        self.crossedSemiContextsLists[leftOrRight] = newCrossedValues

        if  leftOrRight :
            return self.updateContextsAndGetActive(newContextFlag)
            
        else :
            [ newPredictions.update(contextValues[3]) for contextValues in predictionContexts ]

            return numNewContexts, newPredictions 


    def updateContextsAndGetActive(self, newContextFlag):
        """
        This function reviews the list of previously selected left semi-contexts,
        updates the prediction results value of all contexts, including left 
        semi-contexts, creates the list of potentially new contexts resulted from
        intersection between zero-level contexts, determines the contexts that
        coincide with the input data and require activation, prepares the values
        for calculating anomaly value.

        @param newContextFlag:         flag indicating that a new zero-level
                                        context is not recorded at the current
                                        step, which means that all contexts
                                        already exist and there is no need to
                                        create new ones.
        
        @return activeContexts:         list of identifiers of the contexts which
                                        completely coincide with the input stream,
                                        should be considered active and be 
                                        recorded to the input stream of “neurons”

        @return potentialNewContextsLists:  list of contexts based on intersection
                                        between the left and the right zero-level
                                        semi-contexts, which are potentially new
                                        contexts requiring saving to the context
                                        memory


        Эта функция производит обход по списку отобранных ранее левых полуконтекстов,
        обновляет значения результативности предсказывания у всех контекстов, частью
        которых являются данные левые полуконтексты, создаёт список контекстов,
        которые являются результатом пересечения контекстов нулевого уровня и могут
        быть новыми, определяет какие контексты полностью совпали входными данными и
        их надо активировать, подготавливает показатели для расчета величины аномалии. 


        @param newContextsFlag:         флаг, указывающий на то, что на текущем шаге не был
                                        записан новый контекст нулевого уровня, а значит не
                                        нужно создавать путем пересечения новые контексты,
                                        т.к. они все уже созданы ранее
                                                 
        @return activeContexts:         список индентификаторов контекстов, полностью 
                                        совпавших с входным потоком, которые нужно считать
                                        активными и записать во входной поток "нейроны"
                                        
        @return potentialNewContextsLists:    список контекстов, созданных на основе
                                        пересечения левых и правых полуконтекстов нулевого
                                        уровня, и потенциально являющихся новыми
                                        контекстами, которые нужно запомнить в памяти
                                        контекстов
        """

        activeContexts = []
        numSelectedContext = 0
        
        potentialNewContextList = []

        for leftSemiContextValues in self.crossedSemiContextsLists[0] :
        
            for rightSemiContextID, contextID in leftSemiContextValues[3].iteritems() :

                if self.newContextID != contextID :

                    contextValues = self.contextsValuesList[contextID]
                    rightSemiContextValue0,  rightSemiContextValue1, rightSemiContextValue2 = self.semiContextValuesLists[1][rightSemiContextID]
                    
                    if leftSemiContextValues[1] == leftSemiContextValues[2] :           

                        numSelectedContext += 1
                        contextValues[0] += rightSemiContextValue1
                        
                        if rightSemiContextValue2 > 0 :
                            contextValues[1] += rightSemiContextValue2
                                
                            if rightSemiContextValue1 == rightSemiContextValue2 :
                                contextValues[2] += 1
                                activeContexts.append([contextID, contextValues[2], contextValues[5], contextValues[6]])

                            elif contextValues[4] and newContextFlag and leftSemiContextValues[2] <= self.maxLeftSemiContextsLenght :
                                potentialNewContextList.append(tuple([tuple(leftSemiContextValues[0]), tuple(rightSemiContextValue0)]))
                        

                    elif contextValues[4] and newContextFlag and rightSemiContextValue2 > 0 and leftSemiContextValues[2] <= self.maxLeftSemiContextsLenght :
                        potentialNewContextList.append(tuple([tuple(leftSemiContextValues[0]), tuple(rightSemiContextValue0)]))

        self.newContextID = False
        
        return activeContexts, numSelectedContext, potentialNewContextList
