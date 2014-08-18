import os
import argparse

from nab.lib.corpus import Corpus
from nab.lib.util import recur

depth = 3

root = recur(os.path.dirname, os.path.realpath(__file__), depth)

def main(args):

  if not args.absolutePaths:
    args.dataDir = os.path.join(root, args.dataDir)
    if args.destDir:
      args.destDir = os.path.join(root, args.destDir)

  corpus = Corpus(args.dataDir)

  corpus.removeColumn('label', write=True, newRoot=args.destDir)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--destDir",
                    default=None,
                    help="Where you want to store the resulting corpus")

  parser.add_argument("--absolutePaths",
                      help="Whether file paths entered are not relative to \
                      NAB root",
                      default=False,
                      action="store_true")

  args = parser.parse_args()
  main(args)

