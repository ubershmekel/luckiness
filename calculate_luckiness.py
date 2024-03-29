
import re
import csv
import os
import datetime

from mpl_toolkits.mplot3d import Axes3D
import matplotlib as mp
from matplotlib import pyplot as plt
import numpy
from pylab import colorbar

import league

ONLY_TOP = 32
MIN_DATE = datetime.datetime(year=2010, month=1, day=1)
MIN_MATCHES_COUNT = 4


def average(sequence):
    return (1.0 * sum(sequence)) / len(sequence)

    
def plot(x, y, z, sizes=None):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    #ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.jet)
    #ax.plot_wireframe(X, Y, Z, rstride=1, cstride=1, cmap=cm.jet)
    ax.scatter(x,y,z, c=sizes)
    ax.set_zlim3d(0, 1)
    ax.set_ylim3d(0, 1)
    ax.set_xlim3d(0, 1)
    ax.set_xlabel(r'$s_1$')
    ax.set_ylabel(r'$s_2$')
    ax.set_zlabel(r'$P_1$')
    ax.set_xticks([])
    #colorbar()
    plt.show()


def average_distance(prob_p1_wins):
    # (s1, s2, prob, len(rec))
    integral = 0

    num_of_points = len(prob_p1_wins)
    if num_of_points < 5:
        raise Exception("%d points on a graph isn't really useful" % num_of_points)
    
    for s1, s2, prob, count in prob_p1_wins:
        perfect = 1 if s1 > s2 else 0
        integral += abs(perfect - prob)
    
    return 2 * integral / num_of_points
    

'''def get_old_records(league_name):
    records = {}

    # gather all the s1 vs s2 matches
    for pid, player in players_dict.items():
        player_results_fname = os.path.join(league, pid + '.txt')
        results = csv_parse(player_results_fname)
        for match in results:
            opponent_name = match['Opponent']
            date_str = match['Date&nbsp;']
            match_date = datetime.datetime.strptime(date_str, '%y-%m-%d')
            if opponent_name in players_dict and match_date > MIN_DATE:
                opponent = players_dict[match['Opponent']]
                s1 = opponent['skill']
                s2 = player['skill']

                matches = records.get((s1,s2), [])
                #matchesMirror = records.get((s2,s1), [])
                
                if match['Result'] == 'Win':
                    matches.append(1)
                    #matchesMirror.append(0)
                else:
                    matches.append(0)
                    #matchesMirror.append(1)

                records[(s1,s2)] = matches
                #records[(s2,s1)] = matchesMirror
    return records'''

def rating_key(player):
    # negative because python sorts from small to big
    rating = re.findall(r'\d+', player.rating)[0]
    return -int(rating)

def build_skill_graph(ranking, raw_results):
    '''
    ranking = ['tom', 'john', 'luke']
    raw_results = [<Match1>, <Match2>]
    '''
    players_count = len(ranking)
    skill_level = {}

    ranking.sort(key=rating_key)
    
    for i, player in enumerate(ranking):
        skill_level[player.pid] = 1.0 - (1.0 * i) / (players_count - 1)

    players_dict = dict(zip([p.pid for p in ranking], ranking))

    #records = get_old_records(league_name)
    records = {}
    
    # gather all the s1 vs s2 matches
    for match in raw_results:
        date_str = match.date
        player_name = match.p1
        opponent_name = match.p2
        match_date = datetime.datetime.strptime(date_str, '%y-%m-%d')
        
        if opponent_name not in players_dict:
            continue
        if player_name not in players_dict:
            continue
        if match_date < MIN_DATE:
            continue
        
        
        opponent = players_dict[opponent_name]
        #s1 = skill_level[opponent_name]
        #s2 = skill_level[player.pid]
        s1 = skill_level[player_name]
        s2 = skill_level[opponent_name]

        matches_log = records.get((s1,s2), [])
        matchesMirror = records.get((s2,s1), [])
        
        if match.result == 'Win':
            matches_log.append(1)
            matchesMirror.append(0)
        elif match.result == 'Draw':
            matches_log.append(0.5)
            matchesMirror.append(0.5)
        else:
            matches_log.append(0)
            matchesMirror.append(1)

        records[(s1,s2)] = matches_log
        records[(s2,s1)] = matchesMirror

    
    # calculate P(s1, s2) from known s1 v s2 records. P1 = (1win + 1win + 0(loss) + ... ) / total_matches
    prob_p1_wins = []
    matches_count_log = []
    
    for (s1, s2), rec in records.items():
        matches_count = len(rec)
        if matches_count < MIN_MATCHES_COUNT:
            continue
        
        matches_count_log.append(matches_count)
        prob = average(rec)
        # account for s1, s2, probability of winning and the amount of data points
        #dot_size = len(rec)
        expected = 1 if s1 > s2 else 0
        badness = abs(prob - expected) ** 0.5
        prob_p1_wins.append((s1, s2, prob, (badness, 0, 1 - badness)))
    
    return prob_p1_wins


def analyze(league_name):
    target_league = league.League(league_name)
    players_list = target_league.get_players()
    players_list = players_list[:ONLY_TOP]

    raw_results = target_league.get_results()
    prob_p1_wins = build_skill_graph(players_list, raw_results)
    
    luckiness = average_distance(prob_p1_wins)
    print('L for "%s" is %g   Info: top%d, num of points: %d' % 
            (league_name, luckiness, len(players_list), len(prob_p1_wins)))
    # x, y, z = vectors
    
    # limit the skill level shown
    ##prob_p1_wins = [(s1, s2, prob, count) for s1, s2, prob, count in prob_p1_wins if s1 > 0.9]
    
    vectors = zip(*prob_p1_wins)
    vectors = [numpy.array(v) for v in vectors]
    #import pdb;pdb.set_trace()
    plot(*vectors)

print('min matches count: %d, min date: %s' % (MIN_MATCHES_COUNT, MIN_DATE))
analyze('chess')
analyze('coinflip')
analyze('tennis')
analyze('sc1')
analyze('sc2')


