#coding: utf-8

from urllib import urlopen
import itertools
import datetime
import re
import os


from BeautifulSoup import BeautifulSoup
from filecache import filecache


import league


START_DATE = datetime.datetime.now()
#BASE = 'http://tennis.wettpoint.com/en/matchresults/06-07-2011.html'
BASE_URL = 'http://tennis.wettpoint.com/en/matchresults/%s.html'
LEAGUE = 'tennis'

# players.txt is imported from http://www.atpworldtour.com/Rankings/Singles.aspx?d=27.12.2010&c=&r=1#

@filecache(24 * 60 * 60)
def get(url):
    return urlopen(url).read()

def parse_day_file(fname):
    print(fname)
    games_list = league.csv_parse(os.path.join(LEAGUE, fname))
    date_str = match = re.match(r'(\d\d-\d\d-\d\d\d\d)\.txt', fname).groups()[0]
    
    #player_a, player_b, score_a, score_b, game_type, court, match_url
    results_list = []
    for game in games_list:
        for i in range(int(game['score_a'])):
            # p1, p2, result, date
            result = game['player_a'], game['player_b'], 'Win', league.format_date(datetime.datetime.strptime(date_str, '%d-%m-%Y'))
            results_list.append(result)
        for i in range(int(game['score_b'])):
            # p1, p2, result, date
            result = game['player_a'], game['player_b'], 'Loss', league.format_date(datetime.datetime.strptime(date_str, '%d-%m-%Y'))
            results_list.append(result)

    return results_list

def merge_results():
    tennis = league.League(LEAGUE)
    #players_list = tennis.get_players()
    results = []
    for fname in os.listdir(LEAGUE):
        match = re.match(r'(\d\d-\d\d-\d\d\d\d)\.txt$', fname)
        if match:
            results += parse_day_file(fname)
    
    tennis.add_matches(results)
    tennis.flush_matches()

def get_match(match_url):
    html = get(match_url)
    players_str = re.findall(ur'/> ([\w\.\\/ -ö]+) Match Result</h2>', html.decode('iso-8859-1'))[0]
    player_a, player_b = players_str.split(' - ')
    # score <font color="#cc0000"><b>2 : 0</b> (6 : 2) (6 : 4) </font>
    score_a_str, score_b_str = re.findall(r'<font color="#cc0000"><b>(\d) : (\d)', html)[0]
    
    # This Challenger Tour ATP Tennis Match was played on Court Type Hard Court
    game_type, court = re.findall(r'This ([\w ]+?) Tennis Match was played on Court Type <i>(\w+)', html)[0]
    
    # WTA Double Player E.Daniilidou/P.Hercog lost the Match vs. 
    # This WTA Double Tennis Match was played on Court Type 
    return player_a, player_b, score_a_str, score_b_str, game_type, court, match_url

def get_day(when):
    # example url = 'http://tennis.wettpoint.com/en/matchresults/06-07-2011.html'
    date_str = when.strftime('%d-%m-%Y')
    backup_fname = os.path.join(LEAGUE, date_str + '.txt')
    if os.path.isfile(backup_fname):
        return
    
    url = BASE_URL % date_str
    html = get(url)
    print(url)
    match_pages = re.findall(r'(http://tennis.wettpoint.com/en/games/\d+\.html)', html)
    
    # backup urls list
    open(backup_fname + '.urls.txt', 'wb').write('\n'.join(match_pages))
    
    
    fhandle = open(backup_fname, 'wb')
    fhandle.write(b'player_a,player_b,score_a,score_b,game_type,court,match_url\n')
    for match_url in match_pages:
        print(match_url)
        match = get_match(match_url)
        line = u','.join(match) + '\n'
        fhandle.write(line.encode('utf-8'))
        fhandle.flush()
    
    fhandle.close()
    

def get_all_days():
    now = datetime.datetime.now()
    one_day = datetime.timedelta(days=1)
    yesterday = now - one_day
    # 6 months
    for i in range(30 * 6):
        get_day(yesterday - i * one_day)


def convert_names():
    players_list = league.csv_parse(os.path.join(LEAGUE, 'players_full.txt'))
    for player in players_list:
        # "Nadal, Rafael (ESP)"
        # to
        # R. Nadal
        print(player)
        try:
            last_name, first_name = re.findall(ur'([\w ]+), (\w+)', player['pid'])[0]
            player['pid'] = u'%s. %s' % (first_name[0], last_name)
        except Exception, e:
            print('error----',e)
    
    league.csv_save(os.path.join(LEAGUE, 'players.txt'), players_list)

if __name__ == '__main__':
    #get_all_days()
    #merge_results()
    convert_names()
