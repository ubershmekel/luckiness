
from urllib import urlopen
import itertools
from BeautifulSoup import BeautifulSoup
#from lxml import etree
#from pyquery import PyQuery as pq
from filecache import filecache

BASE = 'http://www.teamliquid.net'
PLAYERS_URL = BASE + '/tlpd/sc2-international/players'

@filecache(60 * 60)
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

    open('sc2/%s.txt' % nickname, 'wb').write(record_csv.encode('utf-8'))
    
    return record_csv

def get_players():
    html = get(PLAYERS_URL).decode('utf-8')
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
    csv_list = []
    csv_list.append(','.join(headers_txt))

    for player_row in rows:
        columns = player_row.findAll('td')
        data = [col.text for col in columns]
        href = columns[0].find('a').get('href')
        data += [href]
        csv_list.append(','.join(data))
        nickname = data[0]
        record = get_record(nickname, BASE + href + '/games')
        

    players_csv = '\n'.join(csv_list)

    open('sc2/players.txt', 'wb').write(players_csv.encode('utf-8'))


get_players()
