import spikeforest_widgets as sw
sw.init_electron()

X = sw.Analysis(path='sha1://7219984bab7f8f47afa17bd688807df22846f3d4/analysis.json', download_from='spikeforest.public')
X.show()