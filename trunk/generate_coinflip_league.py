
import os
import string
import random
import datetime

import league

LEAGUE_DIR = 'coinflip'
NUM_OF_PLAYERS = 50
NUM_OF_GAMES = 10


def generate_name():
    return ''.join([random.choice(string.ascii_lowercase) for i in range(random.randint(2,14))])

if __name__ == "__main__":
    
    # generate players set
    players = {generate_name() for i in range(NUM_OF_PLAYERS)}
    
    results = []
    for p1 in players:
        for p2 in players - {p1}:
            for i in range(NUM_OF_GAMES):
                # match = p1, p2, result, date
                result = "Win" if 0.5 < random.random() else "Loss"
                date = datetime.datetime.now().strftime('%y-%m-%d')
                match = p1, p2, result, date
                
                results.append(match)
    
    
    
    coin_league = league.League(LEAGUE_DIR)
    players_dict = league.generate_silly_rating(results)
    coin_league.add_players(players_dict.items())
    coin_league.add_matches(results)
    coin_league.flush()
    
