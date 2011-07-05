
from urllib import urlopen
import itertools
from BeautifulSoup import BeautifulSoup
#from lxml import etree
#from pyquery import PyQuery as pq
from filecache import filecache

import league


BASE = 'http://www.teamliquid.net'
PLAYERS_URL = BASE + '/tlpd/korean/players'
LEAGUE = 'sc1'
#PLAYERS_URL = BASE + '/tlpd/sc2-international/players'
#LEAGUE = 'sc2'

@filecache(24 * 60 * 60)
def get(url):
    return urlopen(url).read()

@filecache(60 * 60)
def get_record(nickname, url):
    print(nickname)
    csv_list = []
    for i in itertools.count():
        print(i)
        html = get(url + '?tabulator_page=%d' % (i + 1))
        soup = BeautifulSoup(html)
        table = soup.find(id='tblt_table')

        rows = table.findAll('tr')
        headers_row = rows[0]
        rows.pop(0)
        headers = headers_row.findAll('th')
        headers_txt = [hdr.text for hdr in headers]
        if len(csv_list) == 0:
            csv_list.append(','.join(headers_txt))

        if len(rows) == 0:
            break
        
        for match_row in rows:
            columns = match_row.findAll('td')
            data = [col.text for col in columns]
            if len(data) < 3:
                raise Exception("strange amount of columns")
            csv_list.append(','.join(data))
        

    record_csv = '\n'.join(csv_list)

    open(LEAGUE + '/%s.txt' % nickname, 'wb').write(record_csv.encode('utf-8'))
    
    return record_csv

def get_players():
    csv_list = []
    player_data = []
    for i in itertools.count():
        html = get(PLAYERS_URL + '?tabulator_page=%d' % (i + 1)).decode('utf-8')
        
        #tree = etree.fromstring(html)
        #d = pq(etree)
        soup = BeautifulSoup(html)

        table = soup.find(id='tblt_table')

        rows = table.findAll('tr')
        headers_row = rows[0]
        rows.pop(0)
        headers = headers_row.findAll('th')
        headers_txt = [hdr.text for hdr in headers]
        headers_txt += ['href']
        
        if len(csv_list) == 0:
            for index, item in enumerate(headers_txt):
                # fix a small issue with teamliquid HTML
                if item == 'ELO&nbsp;':
                    headers_txt[index] = 'rating'
                elif item == 'ID':
                    headers_txt[index] = 'pid'

            csv_list.append(','.join(headers_txt))

        if len(rows) == 0:
            break

        done = False
        for player_row in rows:
            columns = player_row.findAll('td')
            data = [col.text for col in columns]
            href = columns[0].find('a').get('href')
            data += [href]
            ELO = data[4]
            if ELO == '-':
                done = True
                break
            player_data.append(data)
            csv_list.append(','.join(data))
        
        if done:
            break
    
    players_csv = '\n'.join(csv_list)
    open(LEAGUE + '/players.txt', 'wb').write(players_csv.encode('utf-8'))
    
    return player_data
    
def get_records(player_data):
    for data in player_data:
        nickname = data[0]
        href = data[-1]
        record = get_record(nickname, BASE + href + '/games')
            

def merge_results(league_name):
    sc = league.League(league_name)
    players_list = sc.get_players()
    results = []
    for player in players_list:
        try:
            fname = LEAGUE + '/%s.txt' % player.pid
            raw_results = league.csv_parse(fname)
        except Exception, e:
            print('error: %s' % e)
            continue
        #,Date&nbsp;,League,Map,Opponent,Result,
        #p1, p2, result, date = match
        for match in raw_results:
            p1 = player.pid
            p2 = match['Opponent']
            result = match['Result']
            date = match['Date&nbsp;']
            item = p1, p2, result, date
            results.append(item)

    # note that we could clean up the results for duplicates
    # e.g. Player1 beats Player2 appears once in "Player1.txt" and once
    # in "Player2.txt", but this isn't important since 1/2 == 2/4 == 4/8...
    sc.add_matches(results)
    sc.flush_matches()
    

d = get_players()
get_records(d)
merge_results(LEAGUE)
