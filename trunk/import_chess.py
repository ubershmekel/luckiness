
import csv
from urllib import urlopen
import re
import os
import datetime

from filecache import filecache
import mechanize
from BeautifulSoup import BeautifulSoup

import league

LEAGUE = 'chess'
TOURNAMENT_URL_FMT = 'http://chess-results.com/tnr%s.aspx?ix=1&lan=1&turdet=YES&art=%s&iframe=noadv&res=yes&zeilen=99999'

@filecache(24 * 60 * 60)
def get(url):
    return urlopen(url).read()


class EmptyTournamentError(Exception): pass
class StrangeResultError(Exception): pass
class IgnoreResult(Exception): pass

def save_csv(fname, table):
    writer = csv.writer(open(fname, 'wb'))
    for row in table:
        writer.writerow(row)
    

def get_table(soup_table):
    table = []

    # handle headers <th>
    rows_list = soup_table.findAll('tr')
    headers_row = rows_list.pop(0)
    headers = headers_row.findAll('th')
    if len(headers) == 0:
        headers = headers_row.findAll('td')
    headers_txt = [hdr.text for hdr in headers]
    table.append(headers_txt)
    
    for row in rows_list:
        columns = row.findAll('td')
        columns_txt = [col.text for col in columns]
        if len(columns_txt) == 0:
            raise Exception("strange amount of columns")
        table.append(columns_txt)

    return table

@filecache(24 * 60 * 60)
def get_tournament_list_html(firstname, lastname):
    br = mechanize.Browser()
    br.open("http://chess-results.com/SpielerSuche.aspx?lan=1")

    br.select_form(name="aspnetForm")
    # Browser passes through unknown attributes (including methods)
    # to the selected HTMLForm.
    #br["cheeses"] = ["mozzarella", "caerphilly"]  # (the method here is __setitem__)

    # LastName
    #_ctl0_ContentPlaceHolder1_txt_nachname
    br['_ctl0:ContentPlaceHolder1:txt_nachname'] = lastname

    #FirstName
    #_ctl0_ContentPlaceHolder1_txt_vorname
    br['_ctl0:ContentPlaceHolder1:txt_vorname'] = firstname

    #sort should be 1
    #_ctl0_ContentPlaceHolder1_combo_Sort
    br['_ctl0:ContentPlaceHolder1:combo_Sort'] = ['1']

    # Submit current form.  Browser calls .close() on the current response on
    # navigation, so this closes response1
    response = br.submit()

    html = response.read()
    return html

def tournament_fname(tournament_id):
    return os.path.join(LEAGUE, 'tournament-%s.txt' % tournament_id)

def get_tournament_by_type(tournament_id, art):
    # The 'art' url variable stands for tournament table type which is different
    # for different types of tournaments. ffs.
    url = TOURNAMENT_URL_FMT % (tournament_id, art)
    print(url)
    tournament_html = get(url).decode('iso-8859-1')
    
    
    soup = BeautifulSoup(tournament_html)
    tournament_table = []
    
    # headers row = CRg1b
    #html_tables = soup.findAll("table", { "class" : "CRs1" })
    headers_rows = soup.findAll("tr", { "class" : "CRg1b" })
    
    if len(headers_rows) == 0:
        raise EmptyTournamentError
    
    if len(headers_rows[0]) > 1:
        headers_tr = headers_rows[0]
    else:
        headers_tr = headers_rows[1]

    headers = headers_tr.findAll('td')
    headers_txt = [col.text for col in headers]
    tournament_table.append(headers_txt)
    
    if 'Team' in headers_txt:
        # No.	Team	Team	Res.	:	Res.
        # these don't have match info, just team results
        raise EmptyTournamentError
    
    matches_rows = soup.findAll("tr", { "class" : "CRg2" })
    
    if len(matches_rows) == 0:
        raise EmptyTournamentError
    
    date = tournament_date_from_html(tournament_html)
    
    for row in matches_rows:
        columns = row.findAll('td')
        columns_txt = [col.text for col in columns]
        tournament_table.append(columns_txt)

    return tournament_table, date


def get_tournament(tournament_id):
    print(tournament_id)
    
    fname = tournament_fname(tournament_id)
    if os.path.isfile(fname):
        return

    try:
        tournament_table, date = get_tournament_by_type(tournament_id, 2)
    except EmptyTournamentError:
        tournament_table, date = get_tournament_by_type(tournament_id, 3)

    '''
    for table_soup in html_tables:
        data_table = get_table(table_soup)
        headers = data_table.pop(0)
        
        # only add headers once
        if len(tournament_table) == 0:
            if len(headers) == 1:
                # sometimes the 'round #...' is the header
                headers = data_table.pop(0)
            tournament_table.append(headers)

        for row in data_table:
            # ignore the tables that contain "round #..." like tnr26331
            if len(row) > 1:
                tournament_table.append(row)
    '''

    #text = u'\r\n'.join(u','.join(row) for row in tournament_table)
    #open(fname, 'wb').write(text.encode('utf-8'))
    header = tournament_table.pop(0)
    header.append('date')
    for row in tournament_table:
        row.append(date)
    
    tournament_table.insert(0, header)
    
    try:
        save_csv(fname, tournament_table)
    except UnicodeEncodeError, e:
        print('----- %s -----' % e)

def print_error(err_str):
    print('--- error: %s ---' % err_str)

def get_player_tourneys(first_name, last_name):
    html = get_tournament_list_html(first_name, last_name)
    tournament_id_list = re.findall(r'<a href="tnr(\d+)\.aspx', html)
    for tournament_id in tournament_id_list:
        try:
            get_tournament(tournament_id)
        except (IgnoreResult, EmptyTournamentError):
            print_error('empty tournament %s' % tournament_id)
    
def get_all_players():
    players = league.csv_parse(os.path.join(LEAGUE, 'players.txt'))
    #get_player_tourneys('Shakhriyar', 'Mamedyarov')
    for player in players:
        full_name = player['pid']
        print('-' * 40)
        print(full_name)
        last, first = full_name.split(', ')
        get_player_tourneys(first, last)



def tournament_date_from_html(html):
    # 2009/08/08
    date_strings = re.findall(r'(\d\d\d\d/\d\d/\d\d)', html)
    try:
        dates = [datetime.datetime.strptime(date_str, '%Y/%m/%d') for date_str in date_strings]
        oldest = min(dates)
    except ValueError:
        # probably an ongoing or future tournament that doesn't have the date written on it yet
        # like http://chess-results.com/tnr24405.aspx?ix=1&lan=1&turdet=YES&art=3&iframe=noadv&res=yes&zeilen=99999
        # only had: "Last update 8/11/2009 3:29:42 AM"
        print('---- ignoring tourney, no date ----')
        raise IgnoreResult
    return oldest.strftime('%y-%m-%d')

def get_tournament_date_and_url(tournament_id):
    url = TOURNAMENT_URL_FMT % (tournament_id, 2)
    print(url)
    html = get(url)
    return tournament_date_from_html(html), url

def translate_result(res):
    if res in ('0 - 1', '- - +'):
        return 'Loss'
    elif res in ('&frac12; - &frac12;', '- - -'):
        return 'Draw'
    elif res in ('1 - 0', '+ - -'):
        return 'Win'
    # '0 - &frac12;' is probably the points for a by
    elif res in ('1', '0', '', '&frac12;', '0 - &frac12;', '&frac12; - 0', '0 - 0'):
        raise IgnoreResult
    else:
        raise StrangeResultError(res)


def prune_row(p1_index, p2_index, result_i, items):
    try:
        p1 = items[p1_index].lower()
        p2 = items[p2_index].lower()
        match_res = translate_result(items[result_i].strip())
    except IndexError:
        print('--- ignoring row: ---\r\n%s\r\n' % items)
        raise IgnoreResult
    
    date = items[-1]
    return (p1, p2, match_res, date)

def parse_tournament_file(fname):
    global total_tournaments
    global failed
    
    print(fname)
    #txt = open(fname, 'rb').read()
    #lines = txt.splitlines()
    reader = csv.reader(open(fname, 'rb'))
    try:
        headers = next(reader)
    except StopIteration:
        return []
    
    # 9
    #form_a = 'Bo.,No.,,Name,Pts.,Result,Pts.,,Name,No.,date'
    # form_b is the big pain, no way to know anything without good headers....
    matches_list = []
    
    try:
        name_1_i = headers.index('Name')
        name_2_i = headers.index('Name', name_1_i + 1)
        result_i = headers.index('Result')
        for row in reader:
            try:
                match = prune_row(name_1_i, name_2_i, result_i, row)
                matches_list.append(match)
            except IgnoreResult:
                pass
    except ValueError:
        pass
    
    if matches_list == []:
        #form_b = ['Bo.', '24', '&nbsp;&nbsp;SG GABOR SPITTAL 1','Rtg','-','1','&nbsp;&nbsp;DIE KLAGENFURTER 1,Rtg,0 : 4,date'
        form_b = ['Bo.', '1', '&nbsp;&nbsp;Armenien'      , 'Rtg', '-' , '2', '&nbsp;&nbsp;Rest der Welt', 'Rtg', '2&frac12;:3&frac12;', 'date']
        form_c = ['Bo.', '1', '&nbsp;&nbsp;Bosna Sarajewo', '-'  , '20', '&nbsp;&nbsp;Herzlia Chess Club', '5&frac12;: &frac12;', 'date']
        if len(form_b) == len(headers):
            for row in reader:
                try:
                    match = prune_row(2, 6, 8, row)
                    matches_list.append(match)
                except IgnoreResult:
                    pass
 
        if len(form_c) == len(headers):
            for row in reader:
                try:
                    match = prune_row(2, 5, 6, row)
                    matches_list.append(match)
                except IgnoreResult:
                    pass
            
    
    if matches_list == []:
        #raise Exception("unkown form: %s" % headers)
        failed += 1
    
    total_tournaments += 1
    return matches_list
    

def merge_results():
    global failed
    global total_tournaments
    total_tournaments = 0
    failed = 0
    
    files = os.listdir(LEAGUE)
    fhand = open(os.path.join(LEAGUE, 'results.txt'), 'wb')
    writer = csv.writer(fhand)
    writer.writerow('p1,p2,result,date,tournament_id'.split(','))
    for fname in files:
        match = re.findall(r'tournament-(\d+)\.txt', fname)
        if len(match) == 0:
            continue

        tid = match[0]
        #try:
        #    date, url = get_tournament_date_and_url(tid)
        #except IgnoreResult:
        #    continue
        #print(date)
        rows_list = parse_tournament_file(os.path.join(LEAGUE, fname))
        for row in rows_list:
            #match_row = (row[0], row[1], row[2], date.strftime('%y-%m-%d'), url)
            match_row = (row[0], row[1], row[2], row[-1], tid)
            writer.writerow(match_row)
        fhand.flush()
        
    fhand.close()
    print("%s/%s tournaments failed parse" % (failed, total_tournaments))

#get_all_players()
merge_results()

