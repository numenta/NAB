# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import unittest

from nab.util import getProbationPeriod



class CorpusLabelTest(unittest.TestCase):


  def testGetProbationPeriod(self):
    fileLengths = (1000, 4032, 5000, 15000)
    expectedIndices = (150, 604, 750, 750)
    
    for length, idx in zip(fileLengths, expectedIndices):
      probationIndex = getProbationPeriod(0.15, length)
      self.assertEqual(idx, probationIndex, "Expected probation index of {} "
        "got {}.".format(idx, probationIndex))



if __name__ == '__main__':
  unittest.main()
