# ----------------------------------------------------------------------
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
