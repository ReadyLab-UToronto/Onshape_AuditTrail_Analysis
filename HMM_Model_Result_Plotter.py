import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hmmlearn.hmm import MultinomialHMM
import os
from hmmviz import TransGraph


class HMM_model(object):
    def __init__(self, IDString, transmat, startprob, emissionprob, BIC, logLikelihood):
        self.IDString = IDString
        self.transmat = transmat
        self.startprob = startprob
        self.emissionprob = emissionprob
        self.BIC = BIC
        self.logLikelihood = logLikelihood


"""
number = input("List number: ")
fileName = "./HMM_outputs/model" + number + "ResultMatrices.pkl"
with open(fileName, "rb") as file:
    modelResults = pickle.load(file)

np.set_printoptions(precision=2, suppress=True)

nComponent = input("nCmponent? ")
user = input("user? ")
searchString = "nComponents: " + nComponent + " user: " + user
allIterations = input("Print all iterations? (Y/N) ")
if allIterations == "N" or allIterations == "n":
    print("Showing iteration 0 by default")
    searchString = "nComponents: " + nComponent + " user: " + user + " Iteration: " + "0"
print("")
#print(searchString)


for model in modelResults:
    if searchString in model.IDString:
        print(model.IDString)
        print("transmat")
        print(model.transmat)
        print("startprob")
        print(model.startprob)
        print("emissionprob")
        print(model.emissionprob)
        print("BIC")
        print(model.BIC)
        print("Loglikelihood")
        print(model.logLikelihood)
        print("")
"""


# List 3 expert task 1, n = 4
# Lowest BIC
transmat1E = np.array([[0.  , 0.24, 0.  , 0.76],
                       [0.  , 0.61, 0.  , 0.39],
                       [0.52, 0.  , 0.48, 0.  ],
                       [0.6 , 0.  , 0.4 , 0.  ]])
startprob1E = np.array([0., 0., 1., 0.])
emissionprob1E = np.array([[0.  , 0.68, 0.  , 0.32, 0.  , 0.  , 0.  ],
                           [0.85, 0.07, 0.07, 0.  , 0.  , 0.  , 0.  ],
                           [0.78, 0.  , 0.  , 0.  , 0.  , 0.02, 0.19],
                           [0.  , 0.  , 0.67, 0.  , 0.32, 0.  , 0.  ]])

# List 3 expert task 1, n = 6

transmat1E6 = np.array([[0.49, 0.19, 0.  , 0.32, 0.  , 0.  ],
                     [0.  , 0.07, 0.  , 0.  , 0.93, 0.  ],
                     [0.4 , 0.11, 0.04, 0.44, 0.  , 0.01],
                     [0.  , 0.  , 0.7 , 0.03, 0.  , 0.27],
                     [0.36, 0.31, 0.  , 0.33, 0.  , 0.  ],
                     [0.  , 0.  , 0.41, 0.04, 0.  , 0.54]])
startprob =np.array([1., 0., 0., 0., 0., 0.])
emissionprob1E6 = np.array([[0.79, 0.  , 0.  , 0.  , 0.  , 0.02, 0.19],
                         [0.1 , 0.  , 0.  , 0.9 , 0.  , 0.  , 0.  ],
                         [0.  , 0.  , 1.  , 0.  , 0.  , 0.  , 0.  ],
                         [0.  , 1.  , 0.  , 0.  , 0.  , 0.  , 0.  ],
                         [0.03, 0.  , 0.  , 0.  , 0.97, 0.  , 0.  ],
                         [1.  , 0.  , 0.  , 0.  , 0.  , 0.  , 0.  ]])

# list 4 intermetiate task 1, n = 4
transmat1I = np.array([[0.34, 0.05, 0.  , 0.62],
       [0.  , 0.  , 1.  , 0.  ],
       [0.33, 0.5 , 0.17, 0.01],
       [0.71, 0.18, 0.03, 0.08]])
startprob1I = np.array([1., 0., 0., 0.])
emissionprob1I = np.array([[0.53, 0.47, 0.  , 0.  , 0.  , 0.  , 0.  ],
       [0.07, 0.  , 0.  , 0.83, 0.  , 0.  , 0.09],
       [0.18, 0.  , 0.  , 0.  , 0.66, 0.04, 0.12],
       [0.31, 0.  , 0.69, 0.  , 0.  , 0.  , 0.  ]])

# List 5 expert task 2, n = 3
transmat2E = np.array([[0.39, 0.44, 0.17],
                     [0.18, 0.  , 0.82],
                     [0.46, 0.54, 0.  ]])
startprob2E = np.array([1, 0, 0])
emissionprob2E = np.array([[0.91, 0.01, 0.  , 0.  , 0.  , 0.05, 0.03],
                         [0.  , 0.07, 0.  , 0.93, 0.  , 0.  , 0.  ],
                         [0.  , 0.  , 0.06, 0.  , 0.94, 0.  , 0.  ]])


# list 6 intermediate task 2, n = 3
transmat2I = np.array([[0.  , 0.16, 0.84],
                     [0.46, 0.37, 0.17],
                     [0.59, 0.41, 0.  ]])
startprob2I = np.array([0., 1., 0.])
emissionprob2I = np.array([[0.  , 0.03, 0.  , 0.97, 0.  , 0.  , 0.  ],
                         [0.95, 0.  , 0.  , 0.  , 0.  , 0.04, 0.01],
                         [0.  , 0.  , 0.03, 0.  , 0.97, 0.  , 0.  ]])


###########################################################################
#plt.pcolormesh(matrix, cmap="inferno")
#plt.colorbar()
transmatToPlot = transmat1E
emissionToPlot = emissionprob1E

sns.set(rc={'figure.figsize':(11,4)})
fig, (ax1, ax2) = plt.subplots(1,2)
sns.heatmap(transmatToPlot, annot=True, linewidths=1, vmin = 0, vmax = 1, annot_kws={"fontsize":14},
                   cbar=False, ax=ax1, square=True, cmap="hot") # cmap = "" for setting custom cmap
                                #cbar_kws={'label': 'Probability',"orientation":"horizontal"}
sns.heatmap(emissionToPlot, annot=True, linewidths=1, vmin = 0, vmax = 1, annot_kws={"fontsize":14},
                   cbar=True, cbar_kws={'label': 'Probability'}, ax=ax2, cmap="hot") # cmap = "" for setting custom cmap

ax1.set_ylabel("Last State", fontsize = 13)
ax1.set_xlabel("Next State", fontsize = 13)
nComponent = np.shape(transmatToPlot)[0]
ax1.set_xticklabels(range(1,nComponent+1))
ax1.set_yticklabels(range(1,nComponent+1))
ax1.yaxis.tick_left()
ax1.xaxis.tick_top()
ax1.tick_params(length=3)
ax1.xaxis.set_label_position('top')

ax2.set_ylabel("State", fontsize = 15)
emissionTicks = ["Refer to Drawing", "Start Create", "End Create", "Start Edit", "End Edit",
                 "Delete", "Organize"]
ax2.set_yticklabels(range(1,nComponent+1))
ax2.tick_params(length=3)
ax2.yaxis.tick_left()
ax2.xaxis.tick_bottom()
ax2.set_xticklabels(emissionTicks, rotation = 60)

fig.tight_layout()
plt.show()

""" # plotting just one heatmap, old version without tiling both transmat and emissionsmat in one plot
plot = sns.heatmap(matrixToPlot, annot=True, linewidths=1, vmin = 0, vmax = 1, annot_kws={"fontsize":14},
                   cbar_kws={'label': 'Probability'}) # cmap = "" for setting custom cmap
plot.set_xticklabels(range(1,5))
plot.set_yticklabels(range(1,5))
plot.xaxis.set_label_position("top")
plot.xaxis.tick_top()
plt.ylabel("Last State", fontsize = 15)
plt.xlabel("Next State", fontsize = 15)
plt.show()
#xticklabels = False, yticklabels = False
#plot.invert_xaxis() # should be unnecessary
#plot.invert_yaxis() # should be unnecessary
"""








"""
##### For drawing the transition diagrams ####
# https://pypi.org/project/hmmviz/



df = pd.DataFrame(transmatToPlot, columns = ['1','2','3','4'], index=['1','2','3','4'])

print(df)
print("")
graph = TransGraph(df)


# looks best on square figures/axes
fig = plt.figure(figsize=(6, 6))

#nodelabels = {'1':  '☁☀', '2': '😊☂'}

graph.draw(edgelabels=True, nodefontsize=12, nodecolors="blue")
plt.show()
"""



"""
# Alternative way for drawing transition diagrams:
# https://naysan.ca/2020/07/08/drawing-state-transition-diagrams-in-python/
# Import the MarkovChain class from markovchain.py
from markovchain import MarkovChain

trans = np.around(transmatToPlot, decimals=2)
print(trans)

mc = MarkovChain(trans, ['1','2','3','4'])
mc.draw()
"""

