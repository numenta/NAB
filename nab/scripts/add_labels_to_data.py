import os
import argparse

from nab.lib.corpus import Corpus
from nab.lib.labeling import CorpusLabel
from nab.lib.util import recur

depth = 3

root = recur(os.path.dirname, os.path.realpath(__file__), depth)

def main(args):

  if not args.absolutePaths:
    args.labelDir = os.path.join(root, args.labelDir)
    args.dataDir = os.path.join(root, args.dataDir)
    args.destDir = os.path.join(root, args.destDir)

  print args.dataDir
  corpus = Corpus(args.dataDir)
  corpusLabel = CorpusLabel(args.labelDir, corpus=corpus)

  corpusLabel.getEverything()

  corpus.addColumn('label', corpusLabel.rawLabels)

  corpus.copy(args.destDir)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()

  parser.add_argument("--dataDir",
                    default="data",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--labelDir",
                    default="labels",
                    help="This holds all the label windows for the corpus.")

  parser.add_argument("--destDir",
                    help="Where you want to store the resulting corpus")

  parser.add_argument("--absolutePaths",
                      help="Whether file paths entered are not relative to \
                      NAB root",
                      default=False,
                      action="store_true")

  args = parser.parse_args()
  main(args)

