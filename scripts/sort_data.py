#! /usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

