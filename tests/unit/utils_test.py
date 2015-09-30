# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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
