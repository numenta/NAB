# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import random
from nab.detectors.base import AnomalyDetector



class RandomDetector(AnomalyDetector):

  def __init__(self, *args, **kwargs):

    super(RandomDetector, self).__init__(*args, **kwargs)

    self.seed = 42


  def handleRecord(self, inputData):
    """Returns a tuple (anomalyScore).
    The anomalyScore is simply a random value from 0 to 1
    """
    anomalyScore = random.uniform(0,1)
    return (anomalyScore, )


  def initialize(self):
    random.seed(self.seed)
