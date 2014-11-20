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

import math
import unittest2 as unittest
import nab.optimizer


def negativeXSquared(x, args=()):
  """
  Sample x^2 function with arguments as expected by nab.optimizer.twiddle()
  """
  return -x*x


def sine(x, args=()):
  """
  Sample sine function with arguments as expected by nab.optimizer.twiddle()
  """
  return math.sin(x)



class OptimizerTest(unittest.TestCase):


  def test_findsMaximumOfNegativeXSquared(self):
    """
    Test the twiddle function, specfically whether it can find the maximum of
    the negative x squared function. The maximum should be at x=0 with a
    function value of zero.
    Global maximum: x = 0; x^2 = 0
    """
    tolerance = 0.0001
    objectiveFunction = negativeXSquared
    initialGuess = 100

    result = nab.optimizer.twiddle(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = tolerance)

    self.assertTrue(abs(result['parameter'] - 0.0) <= tolerance)
    self.assertTrue(abs(result['score'] - 0.0) <= tolerance**2)


  def test_findsLocalMaximumsOfSine(self):
    """
    Test the twiddle function, specifically whether it can find the local
    maxima of the sine function.
    Local maximum 1: x = pi/2; sin(x) = 1.0
    Local maximum 2: x = 3pi/2; sin(x) = 1.0
    """
    tolerance = 0.0001
    objectiveFunction = sine

    initialGuess = math.pi*(0.5 - 0.1)
    result = nab.optimizer.twiddle(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = tolerance)

    self.assertTrue(abs(result['parameter'] - math.radians(90.0)) <= tolerance)
    self.assertTrue(abs(result['score'] - 1.0) <= tolerance)

    initialGuess = math.pi*(0.5 + 0.1)
    result = nab.optimizer.twiddle(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = tolerance)

    self.assertTrue(abs(result['parameter'] - math.radians(90.0)) <= tolerance)
    self.assertTrue(abs(result['score'] - 1.0) <= tolerance)

    initialGuess = math.pi*(1.5 + 0.1)
    result = nab.optimizer.twiddle(objFunction=objectiveFunction,
      args = (),
      init = initialGuess,
      tolerance = tolerance)

    self.assertTrue(abs(result['parameter'] - math.radians(450.0)) <= tolerance)
    self.assertTrue(abs(result['score'] - 1.0) <= tolerance)



if __name__ == '__main__':
  unittest.main()
