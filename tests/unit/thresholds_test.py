# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import os
import unittest

try:
  import simplejson as json
except ImportError:
  import json

from nab.util import updateThresholds, writeJSON



class ThresholdsTest(unittest.TestCase):
  """Test the functions used in optimizing the anomaly thresholds."""

  def setUp(self):
    oldThresholds = {
      "lucky_detector": {
        "standard": {
          "score": 13.0,
          "threshold": 0.7
        }
      },
      "deep_thought": {
        "standard": {
          "score": 42.0,
          "threshold": 0.9
        }
      }
    }
    root = os.path.dirname(os.path.realpath(__file__))
    self.thresholdsPath = os.path.join(root, "thresholds.json")
    writeJSON(self.thresholdsPath, oldThresholds)


  def tearDown(self):
    if self.thresholdsPath:
      os.remove(self.thresholdsPath)


  def testThresholdUpdateNewDetector(self):
    newThresholds = {
      "bad_detector": {
        "standard": {
          "score": -1.0,
          "threshold": 0.5
        }
      }
    }

    updateThresholds(newThresholds, self.thresholdsPath)

    with open(self.thresholdsPath) as inFile:
      threshDict = json.load(inFile)

    expectedDict = {
      "lucky_detector": {
        "standard": {
          "score": 13.0,
          "threshold": 0.7
        }
      },
      "deep_thought": {
        "standard": {
          "score": 42.0,
          "threshold": 0.9
        }
      },
      "bad_detector": {
        "standard": {
          "score": -1.0,
          "threshold": 0.5
        }
      }
    }

    self.assertDictEqual(expectedDict, threshDict,
      "The updated threshold dict does not match the expected dict.")


  def testThresholdUpdateDifferentScores(self):
    """Thresholds should be overwritten regardless of new scores."""
    newThresholds = {
      "lucky_detector": {
        "standard": {
          "score": 23.0,
          "threshold": 0.77
        }
      },
      "deep_thought": {
        "standard": {
          "score": 32.0,
          "threshold": 0.99
        }
      }
    }

    updateThresholds(newThresholds, self.thresholdsPath)

    with open(self.thresholdsPath) as inFile:
      threshDict = json.load(inFile)

    self.assertDictEqual(newThresholds, threshDict,
      "The updated threshold dict does not match the expected dict.")



if __name__ == '__main__':
  unittest.main()
