from label import LabelCombiner, CorpusLabel

labelRoot = '/Users/jgokhale/Desktop/NAB_local/labels/only_ian'
dataRoot = '/Users/jgokhale/nta/NAB/data'
destPath = '/Users/jgokhale/Desktop/'

LabelCombiner(labelRoot, dataRoot, destPath)


c = CorpusLabel(destPath, dataRoot)

# print c.labels

# print
# print
# print

# print c.windows
