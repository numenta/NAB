import lib.corpus
dataDir = '/Users/jgokhale/nta/NAB/data/'
newDir = '/Users/jgokhale/Desktop/new_data/'
corp = lib.corpus.Corpus(dataDir)

corp.removeColumn('label', write=True, newRoot=newDir)
