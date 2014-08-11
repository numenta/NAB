import sys
import os
import inspect
import math
import unittest2 as unittest

from os.path import dirname, abspath
from pandas.io.parsers import read_csv

# Relative path hacking
sys.path.append(dirname(dirname(abspath(__file__))))

from confusion_matrix import (ConfusionMatrixBase as CMB,
                              pPrintMatrix)


class TestConfusionMatrix(unittest.TestCase):

    def setUp(self):

        self.cMatrix = CMB()

        self.cMatrix.tp = 5
        self.cMatrix.fp = 5
        self.cMatrix.fn = 5
        self.cMatrix.tn = 5
        self.cMatrix.ignored = 0
        self.cMatrix.count = 20

    def testSetPercentages(self):
        

        self.cMatrix.setPercentages()
        self.assertEqual(self.cMatrix.tpp, .25)
        self.assertEqual(self.cMatrix.fpp, .25)
        self.assertEqual(self.cMatrix.fnp, .25)
        self.assertEqual(self.cMatrix.tnp, .25)


    def testSetRates(self):

        self.cMatrix.setRates()

        self.assertEqual(self.cMatrix.tpr, .5)
        self.assertEqual(self.cMatrix.fpr, .5)
        self.assertEqual(self.cMatrix.ppv, .5)
        self.assertEqual(self.cMatrix.fdr, .5)

    def testSetCost(self):


        costMatrix = {"tpCost": 0.0,
                        "fpCost": 50.0,
                        "fnCost": 200.0,
                        "tnCost": 0.0}

        additionalCost = 20

        self.cMatrix.setCost(costMatrix, additionalCost)

        self.assertEqual(self.cMatrix.cost, 1270)

    def testGetTotal(self):

        self.assertEqual(self.cMatrix.getTotal(), 20)

    def testInvalidMatrices(self):

        # Count greater than total
        self.cMatrix.count = 1
        self.assertRaises(Exception, self.cMatrix.setPercentages)

        # One value greater than total
        self.cMatrix.tp = 3
        self.assertRaises(Exception, self.cMatrix.setPercentages)





if __name__ == '__main__':
    unittest.main()