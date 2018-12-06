# this is where the magic happens
# this file will parse UA-generated csv files and save them to models

import csv

# running parse() before uploading a new csv causes an error on the remote build, but not local

# select which file you'd like to parse
# press go and it will parse and print whatever output
# should check to see if objects exist before creating (or overwrite?)

def parse(filename):

    display_txt = []

    with open(filename) as csv_file:  # i'm not sure this will work on our remote hosting
        csv_reader = csv.reader(csv_file, delimiter=',')

        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                # this is the column header rows
                pass
            display_txt.append(row)


            line_count += 1

    return display_txt


