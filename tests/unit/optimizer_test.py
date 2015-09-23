# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
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

"""Tests nab.optimizer for finding the local/global maxima of several 
functions"""

import math
import unittest

from nab.optimizer import twiddle


def negativeXSquared(x, args):
  """
  -(x^2) function, with arguments as expected by nab.optimizer
  Global maximum: x = 0; -(x^2) = 0
  """
  return -x*x


def xSquared(x, args):
  """
  x^2 function, with arguments as expected by nab.optimizer
  Global maximum (unbounded) is infinite
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
  GL function is 1-dimensional optimization test function, evaluated 
  on the domain x=[0.5,2.5]
  Global maximum: x = 2.5; GL(x) = 5.0625
  """
  return math.sin(10*math.pi*x) / (2*x) + (x-1)**4



class OptimizerTest(unittest.TestCase):

  def testMaxOfNegativeXSquared(self):
    """Tests ability to locate the single local/global max
    Optimizer should return 0 at x=0"""
    
    # Start arbitrarily w/in domain
    optimizedThreshold, optimizedScore = twiddle(objFunction=negativeXSquared,
      args = (),
      initialGuess = 42,
      domain = (-50, 50))

    self.assertTrue(abs(optimizedThreshold - 0.0) <= 0.00001,
      "Optimizer returned x = %r, which is not within the tolerance of \
      the maximum location x = 0.0" % optimizedThreshold)
    self.assertTrue(abs(optimizedScore - 0) <= math.sqrt(0.00001),
      "Optimizer returned a max value of %r, but expected 0" % optimizedScore)


  def testMaxOfXSquared(self):
    """Tests ability to locate the max constrained by domain boundaries
    Optimizer should return 100 at x=10"""
    
    # Start right of global min
    optimizedThreshold, optimizedScore = twiddle(objFunction=xSquared,
      args = (),
      initialGuess = 1,
      domain = (0, 10))
      
    self.assertTrue(abs(optimizedThreshold - 10.0) <= 0.00001,
      "Optimizer returned x = %r, which is not within the tolerance of \
      the maximum location x = 10.0" % optimizedThreshold)
    self.assertTrue(abs(optimizedScore - 100) <= math.sqrt(0.00001),
      "Optimizer returned a max value of %r, but expected 100"
      % optimizedScore)


  def testMaxOfSine(self):
    """Tests ability to distinguish between several local/global maxima
    Optimizer should return 1.0 at x={pi/2, 3pi/2}"""

    # Start left of local max pi/2
    optimizedThreshold, optimizedScore = twiddle(objFunction=sine,
      args = (),
      initialGuess = math.pi*(0.5 - 0.1),
      domain = (0, 2*math.pi))

    self.assertTrue(abs(optimizedThreshold - math.pi/2) <= 0.00001,
      "Optimizer returned x = %r, which is not within the tolerance of the \
      maximum location x = %r" % (optimizedThreshold, math.pi/2))
    self.assertTrue(abs(optimizedScore - 1.0) <= 0.00001,
      "Optimizer returned max value of %r, but expected 1.0" % optimizedScore)

    # Start right of local max pi/2
    optimizedThreshold, optimizedScore = twiddle(objFunction=sine,
      args = (),
      initialGuess = math.pi*(0.5 + 0.1),
      domain = (0, 2*math.pi))

    self.assertTrue(abs(optimizedThreshold - math.pi/2) <= 0.00001,
      "Optimizer returned x = %r, which is not within the tolerance of the \
      maximum location x = %r" % (optimizedThreshold, math.pi/2))
    self.assertTrue(abs(optimizedScore - 1.0) <= 0.00001,
      "Optimizer returned max value of %r, but expected 1.0" % optimizedScore)

    # Start left of local min
    optimizedThreshold, optimizedScore = twiddle(objFunction=sine,
      args = (),
      initialGuess = math.pi*(1.5 - 0.1),
      domain = (0, 2*math.pi))

    self.assertTrue(abs(optimizedThreshold - math.pi/2) <= 0.00001,
      "Optimizer returned x = %r, which is not within the tolerance of the \
      maximum location x = %r" % (optimizedThreshold, math.pi/2))
    self.assertTrue(abs(optimizedScore - 1.0) <= 0.00001,
      "Optimizer returned max value of %r, but expected 1.0" % optimizedScore)

    # Start right of local min
    optimizedThreshold, optimizedScore = twiddle(objFunction=sine,
      args = (),
      initialGuess = math.pi*(1.5 + 0.1),
      domain = (0, 3*math.pi))

    self.assertTrue(abs(optimizedThreshold - math.pi*5/2) <= 0.00001,
      "Optimizer returned x = %r, which is not within the tolerance of the \
      maximum location x = %r" % (optimizedThreshold, math.pi*5/2))
    self.assertTrue(abs(optimizedScore - 1.0) <= 0.00001,
      "Optimizer returned max value of %r, but expected 1.0" % optimizedScore)


  def testMaxOfGLFunction(self):
    """Tests limits of the optimizer; not robust enough to find global max 
    amongst many local minima
    Optimizer should return 5.0625 +/- tolerance at x=2.5"""

    # Start right of a local min
    optimizedThreshold, optimizedScore = twiddle(objFunction=GLFunction,
      args = (),
      initialGuess = 1,
      domain = (0.5, 2.5))

    self.assertTrue(abs(optimizedThreshold - 2.5) <= 0.00001,
      "Optimizer returned x = %r, which is not within the tolerance of the \
      maximum location x = 2.5" % optimizedThreshold)
    self.assertTrue(abs(optimizedScore - 5.0625) <= 0.00001,
      "Optimizer returned a max value of %r, but expected 5.0625"
      % optimizedScore)

    # Start at a local max
    optimizedThreshold, optimizedScore = twiddle(objFunction=GLFunction,
      args = (),
      initialGuess = 1.25,
      domain = (0.5, 2.5))

    self.assertFalse(abs(optimizedThreshold - 2.5) <= 0.00001,
      "Optimizer found the max at the correct x = 2.5 but should not have")
    self.assertFalse(abs(optimizedScore - 5.0625) <= 0.00001,
      "Optimizer found the global max value of 5.0625 but should not have")


if __name__ == '__main__':
  unittest.main()
