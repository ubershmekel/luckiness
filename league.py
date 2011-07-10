'''



'''


import csv
import os

PLAYERS_LIST_FNAME = 'players.txt'
RESULTS_LIST_FNAME = 'results.txt'

def format_date(datet):
    return datet.strftime('%y-%m-%d')

def csv_parse(fname):
    reader = csv.reader(open(fname, 'rb'))
    data = []
    header = next(reader)
    header = [item.strip() for item in header]
    for row in reader:
        pairs = zip(header, row)
        element_dict = dict(pairs)
        data.append(element_dict)

    return data

def csv_save(fname, sequence):
    if len(sequence) == 0:
        return
    
    header = sequence[0].keys()
    writer = csv.writer(open(fname, 'wb'))
    writer.writerow(header)
    for obj in sequence[1:]:
        row = [obj[item] for item in header]
        writer.writerow(row)


class Player:
    def __init__(self, pid, rating):
        self.pid = pid
        self.rating = rating

class Match:
    def __init__(self, p1, p2, result, date):
        self.p1 = p1
        self.p2 = p2
        self.result = result
        self.date = date

class League:
    def __init__(self, name):
        self.name = name
            
        self.players = set()
        self.results = []
        
    def get_players(self):
        player_dict = csv_parse(os.path.join(self.name, PLAYERS_LIST_FNAME))
        players_list = []
        for player in player_dict:
            players_list.append(Player(pid=player['pid'], rating=player['rating']))
        return players_list

    def get_results(self):
        results_dict = csv_parse(os.path.join(self.name, RESULTS_LIST_FNAME))
        results_list = []
        for m in results_dict:
            results_list.append(Match(p1=m['p1'], p2=m['p2'], result=m['result'], date=m['date']))
        return results_list
        
        
    def add_players(self, players_list):
        for player in players_list:
            pid, rating = player
            self.players.add(player)
            
    def add_matches(self, match_results):
        '''
               #    p1, p2, result, date = match
        '''
        self.results = match_results
        #for match in match_results:
        #    p1, p2, result, date = match
        #    p1_results = self.results.get(p1, [])
        #    p1_results.append(match)
        #    results[p1] = p1_results
        #    
        #    p2_results = self.results.get(p2, [])
        #    p2_results.append(match)
        #    results[p2] = p2_results

    def flush_players(self):
        text = 'pid,rating\n'
        text += '\n'.join(["%s,%s" % (pid, elo) for pid, elo in self.players])
        open(os.path.join(self.name, PLAYERS_LIST_FNAME), 'wb').write(text.encode('utf-8'))

    def flush_matches(self):
        results_text = 'p1,p2,result,date\n'
        str_lines = [','.join(result) for result in self.results]
        results_text += '\n'.join(str_lines)
        # python 3 vs python 2
        try:
            results_bin = results_text.encode('utf-8')
        except UnicodeDecodeError:
            results_bin = results_text
            
        open(os.path.join(self.name, RESULTS_LIST_FNAME), 'wb').write(results_bin)
    
    def flush(self):
        if not os.path.isdir(self.name):
            os.mkdir(self.name)

        self.flush_players()
        self.flush_matches()
        
        #for player in self.players:
            #pid, rating = player
            #record_text = 'Date,Player1,Player2,Result\n'
            ##record_text += '\n'.join(["%s,%s,%s" % (date, opponent, result) for date, opponent, result in matches])
            ##open(os.path.join(self.name, pid + '.txt'), 'wb').write(record_text.encode('utf-8'))
            #record_text += '\n'.join([','.join(match) for match in self.results])
            #open(os.path.join(self.name, pid + '.txt'), 'wb').write(record_text.encode('utf-8'))
    
def generate_silly_rating(results):
    wins = {}
    for p1, p2, result, date in results:
        if result == "Win":
            score = wins.get(p1, 0)
            wins[p1] = score + 1
    return wins
        

