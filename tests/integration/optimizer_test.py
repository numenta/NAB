# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

"""Tests nab.optimizer for finding the local/global maxima of several functions"""

import math
import unittest

import nab.optimizer



def negativeXSquared(x, args):
  """
  -(x^2) function, with arguments as expected by nab.optimizer
  Global maximum: x = 0; x^2 = 0
  """
  return -x*x


def xSquared(x, args):
  """
  """
  return x*x

def sine(x, args):
  """
  sine function, with arguments as expected by nab.optimizer
  Local maximum 1: x = pi/2; sin(x) = 1.0
  Local maximum 2: x = 3pi/2; sin(x) = 1.0
  """
  return math.sin(x)


def GLFunction(x, args):
  """
  Gramacy & Lee function, with arguments as expected by nab.optimizer
  GL function is 1-dimensional optimization test function, evaluated on the domain x=[0.5,2.5]
  Global maximum: x = 2.5; GL(x) = 5.0625
  """
  return math.sin(10*math.pi*x) / (2*x) + (x-1)**4



class OptimizerTest(unittest.TestCase):

  def setUp(self):
    self.optimizer = nab.optimizer.twiddle
    self.tolerance = 0.00001


  def testMaxOfNegativeXSquared(self):
    """Tests ability to locate the single local/global max
    Optimizer should return 0 at x=0"""
    objectiveFunction = negativeXSquared
    
    # Start arbitrarily w/in domain
    initialGuess = 42

    result = self.optimizer(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = self.tolerance,
      domain = (-50, 50))

    self.assertTrue(abs(result['parameter'] - 0.0) <= self.tolerance, "Optimizer returned x = %r, which is not within the tolerance of the maximum location x = %r" % (result['parameter'], 0.0))
    self.assertTrue(abs(result['score'] - 0) <= math.sqrt(self.tolerance),  "Optimizer returned a max value of %r, but expected %r" % (result['score'], 0))


  def testMaxOfXSquared(self):
    """Tests ability to locate the max constrained by domain boundaries
    Optimizer should return 100 at x=10"""
    objectiveFunction = xSquared
    
    # Start right of global min
    initialGuess = 1
    
    result = self.optimizer(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = self.tolerance,
      domain = (0, 10))
      
    self.assertTrue(abs(result['parameter'] - 10.0) <= self.tolerance, "Optimizer returned x = %r, which is not within the tolerance of the maximum location x = %r" % (result['parameter'], 10.0))
    self.assertTrue(abs(result['score'] - 100) <= math.sqrt(self.tolerance),  "Optimizer returned a max value of %r, but expected %r" % (result['score'], 100))


  def testMaxOfSine(self):
    """Tests ability to distinguish between several local/global maxima
    Optimizer should return 1.0 at x={pi/2, 3pi/2}"""
    objectiveFunction = sine

    # Start left of local max pi/2
    initialGuess = math.pi*(0.5 - 0.1)
    
    result = self.optimizer(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = self.tolerance,
      domain = (0, 2*math.pi))

    self.assertTrue(abs(result['parameter'] - math.pi/2) <= self.tolerance, "Optimizer returned x = %r, which is not within the tolerance of the maximum location x = %r" % (result['parameter'], math.pi/2))
    self.assertTrue(abs(result['score'] - 1.0) <= self.tolerance, "Optimizer returned max value of %r, but expected %r" % (result['score'], 1.0))

    # Start right of local max pi/2
    initialGuess = math.pi*(0.5 + 0.1)
    
    result = self.optimizer(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = self.tolerance,
      domain = (0, 2*math.pi))

    self.assertTrue(abs(result['parameter'] - math.pi/2) <= self.tolerance, "Optimizer returned x = %r, which is not within the tolerance of the maximum location x = %r" % (result['parameter'], math.pi/2))
    self.assertTrue(abs(result['score'] - 1.0) <= self.tolerance, "Optimizer returned max value of %r, but expected %r" % (result['score'], 1.0))

    # Start left of local min
    initialGuess = math.pi*(1.5 - 0.1)
    
    result = self.optimizer(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = self.tolerance,
      domain = (0, 2*math.pi))

    self.assertTrue(abs(result['parameter'] - math.pi/2) <= self.tolerance, "Optimizer returned x = %r, which is not within the tolerance of the maximum location x = %r" % (result['parameter'], math.pi/2))
    self.assertTrue(abs(result['score'] - 1.0) <= self.tolerance, "Optimizer returned max value of %r, but expected %r" % (result['score'], 1.0))

    # Start right of local min
    initialGuess = math.pi*(1.5 + 0.1)
    
    result = self.optimizer(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = self.tolerance,
      domain = (0, 3*math.pi))

    self.assertTrue(abs(result['parameter'] - math.pi*5/2) <= self.tolerance, "Optimizer returned x = %r, which is not within the tolerance of the maximum location x = %r" % (result['parameter'], math.pi*5/2))
    self.assertTrue(abs(result['score'] - 1.0) <= self.tolerance, "Optimizer returned max value of %r, but expected %r" % (result['score'], 1.0))


  def testMaxOfGLFunction(self):
    """Tests limits of the optimizer; not robust enough to find global max amongst many local minima
    Optimizer should return 5.0625 +/- tolerance at x=2.5"""
    objectiveFunction = GLFunction

    # Start right of a local min
    initialGuess = 1
    result = self.optimizer(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = self.tolerance,
      domain = (0.5, 2.5))

    self.assertTrue(abs(result['parameter'] - 2.5) <= self.tolerance, "Optimizer returned x = %r, which is not within the tolerance of the maximum location x = %r" % (result['parameter'], 2.5))
    self.assertTrue(abs(result['score'] - 5.0625) <= self.tolerance, "Optimizer returned a max value of %r, but expected %r" % (result['score'], 5.0625))

    # Start at a local max
    initialGuess = 1.25
    result = self.optimizer(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = self.tolerance,
      domain = (0.5, 2.5))

    self.assertFalse(abs(result['parameter'] - 2.5) <= self.tolerance, "Optimizier found the max at the correct x = %r but should not have" % 2.5)
    self.assertFalse(abs(result['score'] - 5.0625) <= self.tolerance, "Optimizer found the global max value of %r but should not have" % 5.0625)


if __name__ == '__main__':
  unittest.main()
