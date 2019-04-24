import csv

file = open('media/Thunder2018_AllGames.csv', 'r+')
csv_reader = csv.DictReader(file, delimiter=',')

all_actions = []
for row in csv_reader:
    if row['Action'] not in all_actions:
        all_actions.append(row['Action'])

print(all_actions)