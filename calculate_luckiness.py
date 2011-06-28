

import csv
import os

from mpl_toolkits.mplot3d import Axes3D
import matplotlib as mp
from matplotlib import pyplot as plt
import numpy
from pylab import colorbar

ONLY_TOP = 16

def average(sequence):
    return (1.0 * sum(sequence)) / len(sequence)

def csv_parse(fname):
    reader = csv.reader(open(fname, 'rb'))
    data = []
    header = next(reader)
    for row in reader:
        pairs = zip(header, row)
        element_dict = dict(pairs)
        data.append(element_dict)

    return data
    

def plot(x, y, z, sizes=None):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    #ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.jet)
    #ax.plot_wireframe(X, Y, Z, rstride=1, cstride=1, cmap=cm.jet)
    ax.scatter(x,y,z, s=sizes)
    ax.set_zlim3d(0, 1)
    ax.set_ylim3d(0, 1)
    ax.set_xlim3d(0, 1)
    ax.set_xlabel(r'$s_1$')
    ax.set_ylabel(r'$s_2$')
    ax.set_zlabel(r'$P_1$')
    ax.set_xticks([])
    #colorbar()
    plt.show()


def calculate_luckiness(prob_p1_wins):
    # (s1, s2, prob, len(rec))
    integral = 0
    
    for s1, s2, prob, count in prob_p1_wins:
        perfect = 1 if s1 > s2 else 0
        integral += abs(perfect - prob)
    
    return 2 * integral / len(prob_p1_wins)
    

def analyze(league):
    players_fname = os.path.join(league, 'players.txt')
    players_list = csv_parse(players_fname)
    players_list = players_list[:ONLY_TOP]
    
    for i, player in enumerate(players_list):
        player['skill'] = 1.0 - (1.0 * i) / (ONLY_TOP - 1)

    players_dict = dict(zip([p['ID'] for p in players_list], players_list))

    records = {}

    # gather all the s1 vs s2 matches
    for pid, player in players_dict.items():
        player_results_fname = os.path.join(league, pid + '.txt')
        results = csv_parse(player_results_fname)
        for match in results:
            if match['Opponent'] in players_dict:
                opponent = players_dict[match['Opponent']]
                s1 = opponent['skill']
                s2 = player['skill']

                matches = records.get((s1,s2), [])
                matchesMirror = records.get((s2,s1), [])
                
                if match['Result'] == 'Win':
                    matches.append(1)
                    matchesMirror.append(0)
                else:
                    matches.append(0)
                    matchesMirror.append(1)

                records[(s1,s2)] = matches
                records[(s2,s1)] = matchesMirror
        

    # calculate P from known s1 v s2 records. P1 = (1win + 1win + 0(loss) + ... ) / total_matches
    prob_p1_wins = []
    for (s1, s2), rec in records.items():
        if len(rec) < 5:
            continue
        prob = average(rec)
        # account for s1, s2, probability of winning and the amount of data points
        prob_p1_wins.append((s1, s2, prob, len(rec)))

    
    luckiness = calculate_luckiness(prob_p1_wins)
    print('L for "%s" is: %g' % (league, luckiness))
    # x, y, z = vectors
    prob_p1_wins = [(s1, s2, prob, count) for s1, s2, prob, count in prob_p1_wins if s1 > 0.9]
    vectors = zip(*prob_p1_wins)
    vectors = [numpy.array(v) for v in vectors]
    #import pdb;pdb.set_trace()
    #plot(*vectors)

analyze('sc1')
analyze('sc2')
