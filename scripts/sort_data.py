#! /usr/bin/env python
# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import argparse
import os
import pandas

from nab.util import recur, checkInputs

depth = 2
root = recur(os.path.dirname, os.path.realpath(__file__), depth)

def sortData(input_filename, output_filename):
  df = pandas.read_csv(input_filename)
  df.sort(columns='timestamp', inplace=True)
  return df.to_csv(output_filename, index=False)


def main(args):

  if not args.absolutePaths:
    args.dataDir = os.path.join(root, args.dataDir)
    args.destDir = os.path.join(root, args.destDir)

  if not checkInputs(args):
    return

  if not os.path.exists(args.destDir):
    os.makedirs(args.destDir)

  datafiles = [f for f in os.listdir(args.dataDir) if f.endswith(".csv")]

  for datafile in datafiles:
    input_filename = os.path.join(args.dataDir, datafile)
    output_filename = os.path.join(args.destDir, datafile)
    sortData(input_filename, output_filename)

  print("Sorted files written to ", args.destDir)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("--dataDir",
                      default="data",
                      help="This holds the datafiles to be sorted.")

  parser.add_argument("--destDir",
                      help="Where you want to store the resulting sorted data?")

  parser.add_argument("--absolutePaths",
                      help="Whether file paths entered are not relative to "
                      "NAB root",
                      default=False,
                      action="store_true")

  args = parser.parse_args()
  main(args)

