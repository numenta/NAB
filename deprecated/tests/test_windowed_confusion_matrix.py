import sys
import os
import inspect
import math
import unittest2 as unittest

from os.path import dirname, abspath
from pandas.io.parsers import read_csv

# Relative path hacking
sys.path.append(dirname(dirname(abspath(__file__))))

from confusion_matrix import (WindowedConfusionMatrix as CM,
                              pPrintMatrix)


class TestWindowedConfusionMatrix(unittest.TestCase):

    def setUp(self):

        self.window = 120
        self.windowStepSize = 5
        self.windowRecordCount = self.window / self.windowStepSize

        self.costMatrix = {"tpCost": 0.0,
                           "fpCost": 50.0,
                           "fnCost": 200.0,
                           "tnCost": 0.0}

        self.latePenalty = (.5 * self.costMatrix["fnCost"]) \
                           / self.windowRecordCount

    def testSingleAnomalousRecordNoLag(self):
        """
        One record is anomalous, and is immediately labeled as such
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)
        self.assertEqual(cMatrix.cost, 0)

    def testSingleAnomalousRecord1Lag(self):
        """
        The label now lags the actual anomaly by one record. A small latePenalty
        should be added.
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)

        expectedCost = math.floor(self.latePenalty)
        self.assertEqual(cMatrix.cost, expectedCost)

    def testSingleAnomalousRecord23Lag(self):
        """
        Label is just at the end of the allowed window. Late penalty should be
        at max.
        """


        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)

        expectedCost = math.floor(self.latePenalty * 23) 
        self.assertEqual(cMatrix.cost, expectedCost)

    def testSingleAnomalousRecord24Lag(self):
        """
        Label is now outside the allowed window. Should be a FN + FP
        """


        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 0)
        self.assertEqual(cMatrix.fp, 1)
        self.assertEqual(cMatrix.fn, 1)

        expectedCost = self.costMatrix['fnCost'] + self.costMatrix['fpCost']
        self.assertEqual(cMatrix.cost, expectedCost)

    def testSingleAnomalousRecord1Spam(self):
        """
        Label is correct, but we get one fp during the suppression period
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)
        self.assertEqual(cMatrix.fp, 1)

        expectedCost = self.costMatrix['fpCost']
        self.assertEqual(cMatrix.cost, expectedCost)

    def testSingleAnomalousRecordManySpam(self):
        """
        Label is correct, but we get several fp during the suppression period
        which should all be treated as one fp
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)
        self.assertEqual(cMatrix.fp, 1)

        expectedCost = self.costMatrix['fpCost']
        self.assertEqual(cMatrix.cost, expectedCost)

    def testTwoRecordAnomalyNoLag(self):
        """
        The anomaly is labeled over two records and caught on the first.
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)
        self.assertEqual(cMatrix.cost, 0)

    def testTwoRecordAnomaly1Lag(self):
        """
        The anomaly is labeled over two records and caught on the second. 
        There should be a small latePenalty
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)

        expectedCost = math.floor(self.latePenalty)
        self.assertEqual(cMatrix.cost, expectedCost)

    def testTwoRecordAnomaly23Lag(self):
        """
        Label is just at the end of the allowed window. Late penalty should be
        at max.
        """


        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)

        expectedCost = math.floor(self.latePenalty * 23) 
        self.assertEqual(cMatrix.cost, expectedCost)

    def testTwoRecordAnomaly24Lag(self):
        """
        Label is now outside the allowed window. Should be a FN + FP
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 0)
        self.assertEqual(cMatrix.fp, 1)
        self.assertEqual(cMatrix.fn, 1)

        expectedCost = self.costMatrix['fnCost'] + self.costMatrix['fpCost']
        self.assertEqual(cMatrix.cost, expectedCost)

    def testSecondAnomalyInSuppressionPeriod(self):
        """
        We catch the first anomaly and there is a second which is not labeled.
        This is good because anything in the suppression period is spam.
        """
        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)
        self.assertEqual(cMatrix.fn, 0)
        self.assertEqual(cMatrix.cost, 0)

    def testSecondAnomalyInSuppressionPeriodLabeled(self):
        """
        We catch the first anomaly and there is a second which *is* labeled.
        This is spam.
        """
        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)
        self.assertEqual(cMatrix.fp, 1)
        expectedCost = self.costMatrix['fpCost']
        self.assertEqual(cMatrix.cost, expectedCost)

    def testSecondAnomalyOutsideSuppressionPeriodLabeled(self):
        """
        Once the suppression period ends we should pay attention to anomalies 
        again
        """
        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 2)
        self.assertEqual(cMatrix.cost, 0)

    def testSecondAnomalyOutsideSuppressionPeriodUnlabeled(self):
        """
        Once the suppression period ends we should pay attention to anomalies 
        again
        """
        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)
        self.assertEqual(cMatrix.fn, 1)
        expectedCost = self.costMatrix['fnCost']
        self.assertEqual(cMatrix.cost, expectedCost)

    def testLongContinualAnomaly(self):
        """
        If a long anomaly is labeled every suppression period records then
        these should each be TPs.

        NOTE: This test also has an interesting edge case. 

        Row 64 is outside the second suppression period. However it is never
        "caught" as an anomaly. This is *NOT* labeled a False Negative because
        we run out of records before we run out the allowed window. This is
        correct behavior.
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 2)
        self.assertEqual(cMatrix.cost, 0)

    def testLongContinualAnomalySpam(self):
        """
        If a long anomaly is labeled every record we should count one fp
        per suppression period

        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 3)
        self.assertEqual(cMatrix.fp, 2)
        expectedCost = self.costMatrix['fpCost'] * 2
        self.assertEqual(cMatrix.cost, expectedCost)

    def testPlateauAnomaly(self):
        """
        A plateau less than two hours long. Caught immediately.
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)
        self.assertEqual(cMatrix.fp, 0)
        self.assertEqual(cMatrix.cost, 0)

    def testLongPlateauAnomaly(self):
        """
        A long plateau. This becomes the new normal and is not flagged.
        The drop off should also not be flagged.
        """

        mName = inspect.stack()[0][3]
        cMatrix = self.getMatrix(mName)

        self.assertEqual(cMatrix.tp, 1)
        self.assertEqual(cMatrix.fp, 0)
        self.assertEqual(cMatrix.cost, 0)

    def getMatrix(self, mName):
        """
        Returns the confusion matrix by loading mName.csv and instantiating
        a new confusion matrix
        """
        inputFile = os.path.join('data', mName + ".csv")
        with open(inputFile) as fh:
            df = read_csv(fh)

        actual = df.label
        predicted = df.anomaly_score

        cMatrix = CM(predicted,
                     actual,
                     self.window,
                     self.windowStepSize,
                     self.costMatrix)

        return cMatrix



if __name__ == '__main__':
    unittest.main()