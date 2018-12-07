# this is where the magic happens
# this file will parse UA-generated csv files and save them to models

import csv
from . import models

# running parse() before uploading a new csv causes an error on the remote build, but not local

# select which file you'd like to parse
# press go and it will parse and print whatever output
# should check to see if objects exist before creating (or overwrite?)

def parse(filename):

    display_txt = []

    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                # this is the column header rows
                pass
            display_txt.append(row)


            line_count += 1

    return display_txt


"""

## One per game columns:
# Date/Time
# Tournament
# Opponent
# 
## One per point columns:
# Line (refers to starting fence)
# Our Score EOP
# Their Score EOP
# 
## One per possession columns:
# Players # this is tracked per-point but we know it should be per (possession or event?)
#         # we are storing this as per-event
#
#
## One per event columns:
# Event Type
# Action
# Passer
# Receiver
# Hang Time
# Elapsed Time (sec)


line 0 is column headers
line 1 - get first three values, create Game

for each line after 0:
    # check if new point
    if (our score EOP + their score EOP) > previous_score_total:
        save Point
        create new Point, fetch current_point_ID
        set non-key vars
        handle_new_possession()
        
             
    # check if new possession
    elif (this_event_type != previous_event_type)
        save Possession
        handle_new_possession()
    

    create new Event
    for player in column x through to column x + 27:
        playerpk = handle_player(player)
        create relationship as part of the ManyToMany "players_onfield"
        set point_possession_ID to current_possession_ID
        
    if defender:
        fetch defender
    else:
        fetch passer and receiver
    set non key vars    
    
    set previous_event_type to event_type
    save event
    set previous_score_total = our_score_EOP + their_score_EOP

def handle_new_possession()
    create new Possession
    set current_possession_point_ID to current_point_ID 
    set non-key vars
    save possession

def handle_player(player)
    # check if a Player object for this player exists
    
    ## HOW WILL WE HANDLE PLAYERS HAVING DIFFERENT NAMES IN DIFF UA IMPORTS
    ## but actually being the same person?
    ### some kind of table lookup to convert nicknames into new, real names?
    ### when people are uploading, ask them to search our DB for existing players then match them up?
    
    #### MVP - assume input name is for reals name 
    
    if yes:
        return player pk
    else:
        create new Player object
        save player
        return player pk
    

"""
