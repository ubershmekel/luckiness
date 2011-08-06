import csv

r = csv.reader(open('players.txt', 'rb'))

table = list(r)
header = table.pop(0)
for row in table:
    row[1] = row[1].replace(',', '')

w = csv.writer(open('players.txt', 'wb'))
w.writerows([header] + table)
