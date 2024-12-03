# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
Adaptive Resonance Theory detector - Open Source Edition
2021, Mark Hampton   mark.hampton@ieee.org
See https://github.com/MarkNZed/ARTimeNAB
"""

from nab.detectors.base import AnomalyDetector

class ARTimeDetector(AnomalyDetector):

    # To use a private GitHub repo needed:
    #  export JULIA_SSH_NO_VERIFY_HOSTS=domain.com
    #  for SSH ssh-add to ssh-agent to have julia git login via ssh
    #  for https login see https://docs.github.com/en/get-started/getting-started-with-git/caching-your-github-credentials-in-git

    def __init__(self, *args, **kwargs):
        super(ARTimeDetector, self).__init__(*args, **kwargs)
        # import here so we install ARTime only once
        from juliacall import Main as jl

    def initialize(self):
        # Needed to place juliacall here so we get a separate instance in each Python process
        from juliacall import Main as jl
        jl.seval("using ARTime")
        jl.seval("p = ARTime.P()")
        jline = "ARTime.init(%s, %s, %s, p)" % (self.inputMin, self.inputMax, self.dataSet.data.shape[0])
        jl.seval(jline)
        self.jl = jl
        
    def handleRecord(self, inputData):
        value = inputData["value"]
        anomalyScore = getattr(self.jl.ARTime, "process_sample!")(value, self.jl.p)
        return (anomalyScore,)
