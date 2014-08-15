#!/usr/bin/env python



import os
from os.path import dirname, realpath
import argparse

from nab.lib.labeling import LabelCombiner

def main(args):

  root = dirname(dirname(dirname(realpath(__file__))))

  params = [
    os.path.join(root, args.labelDir),
    os.path.join(root, args.dataDir)]

  if args.threshold:
    params.append(args.threshold)

  labelCombiner = LabelCombiner(*tuple(params))

  labelCombiner.combine()

  labelCombiner.write(args.destDir)

  print "Labels Directory: %s" % args.labelDir
  print "Data Directory: %s" % args.dataDir
  print "Destination Directory: %s" % args.destDir


if __name__ == '__main__':
  parser = argparse.ArgumentParser()

  parser.add_argument("--labelDir",
                    help="This directory holds all the individual labels")

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus")

  parser.add_argument("--destDir",
                    help="Where you want to store the combined labels",
                    default="labels",
                    action="store_true")

  args = parser.parse_args()

  # main()

