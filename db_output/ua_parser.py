# this is where the magic happens
# this file will parse UA-generated csv files and save them to models

import csv
from . import models


def get_player_names(filename):
    # shorter version that pulls out every player mentioned in the stats
    # used for manual data validation

    csv_file = open(filename)
    csv_reader = csv.DictReader(csv_file, delimiter=',')

    player_name_list = []
    for line in csv_reader:
        for x in range(0, 27):
            num = 'Player ' + str(x)
            if line[num] not in player_name_list:
                player_name_list.append(line[num])

    return player_name_list


# running parse() before uploading a new csv causes an error on the remote build, but not local

# select which file you'd like to parse
# press go and it will parse and print whatever output

# should check to see if objects exist before creating (or overwrite?)
# this currently doesn't check at all to see if anything exists
# imo should check that right at the start and stop ?
# how to identify?

## One per game columns:
# Date/Time
# Tournament
# Opponent
#
## One per point columns:
# Line (refers to starting fence)
# Our Score EOP
# Their Score EOP
# Point Elapsed Seconds
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


def parse(filename, conversion_dict):
    # should also be taking in any data that is required that cannot be pulled from the file
    # team_name
    # conversion_dict (see bottom)
    # optional: opposing game/team




    csv_file = open(filename)
    csv_reader = csv.DictReader(csv_file, delimiter=',')
    # DictReader means that each line is a dictionary, with name:value determined by column name:column value

    # valid column names from ua csv are:

    # Date/Time,Tournamemnt,Opponent,Point Elapsed Seconds,Line,Our Score - End of Point,Their Score - End of Point,
    # Event Type,Action,Passer,Receiver,Defender,Hang Time (secs),Elapsed Time (secs),

    # Player 0,Player 1,Player 2,Player 3,Player 4,Player 5,Player 6,Player 7,Player 8,Player 9,Player 10,Player 11,
    # Player 12,Player 13,Player 14,Player 15,Player 16,Player 17,Player 18,Player 19,Player 20,Player 21,Player 22,
    # Player 23,Player 24,Player 25,Player 26,Player 27,

    # # below are unused
    # Begin Area,Begin X,Begin Y,End Area,End X,End Y,Distance Unit of Measure,Absolute Distance,Lateral Distance,Toward Our Goal Distance

    indexed_lines = list(enumerate(csv_reader)) # i wonder if this is memory inefficient?
    # indexed_lines[index] returns (index,line) tuple

    for index, line in indexed_lines:

        # block 1: first time through initialisation

        if index == 0:

            this_game = models.Game()
            this_game.datetime = line['Date/Time']
            this_game.tournament_name = line['Tournamemnt']  # UA csv has typo in column name "Tournamemnt"

            # NEED TO SET TEAM
            # where can pull team name from - additional data required


            this_game.save()

            # how to set opposing game deatils and stuff
            # manually subsequently?
            # line['Opponent']
            # check if an appropriate Opponent object exists
            # if not, create it and insert. if yes, insert.

            this_point = handle_new_point(this_game.game_ID, line)
            this_possession = handle_new_possession(this_point.point_ID)

        # block 2: checks for new point or new possession
        # should never be continuing in this block, or handling event-specific data
        # this block is for containers only

        if index > 0: # first event will not require a new possession or point, those are already done
                        # if either score has increased:
            points_completed = line['Our Score - End of Point'] + line['Their Score - End of Point']
            prev_points_completed = indexed_lines[index-1][1]['Our Score - End of Point'] +\
                                    indexed_lines[index-1][1]['Their Score - End of Point']

            if points_completed > prev_points_completed:
                this_point.save()
                this_possession.save()

                this_point = handle_new_point(this_game.game_ID, line) # will never be half at end of first point
                this_possession = handle_new_possession(this_point.point_ID)

            elif line['Event Type'] != indexed_lines[index-1][1]['Event Type']: # new possession but not new point
                this_possession.save()

                this_possession = handle_new_possession(this_point.point_ID)

            else:
                pass # neither new point nor new possession

        # block 3: event handling

        # valid Actions - from ThunderAllGames: # potentially more - how to get all possible?
        #
        # Event Type:
        #   Defense:
        #       Pull, PullOB, D
        #   Offense:
        #       Catch, Drop, Stall
        #   either:
        #       Goal, Throwaway

        # block 3a: check + store players

        player_col_list = []
        for x in range(0,27):
            col = 'Player '+str(x)
            player_col_list.append(col)

        this_event = handle_new_event(this_possession.possession_ID,line)

        for player_col in player_col_list:
            if line[player_col]:
                player = handle_check_player(conversion_dict[line[player_col]])
                this_event.players.add(player)  # this is building the manytomany
                this_event.save()

        if line['Defender']:
            this_event.defender = handle_check_player(conversion_dict[line['Defender']])
        else:
            this_event.passer = handle_check_player(conversion_dict[line['Passer']])
            this_event.receiver = handle_check_player(conversion_dict[line['Receiver']])

        this_event.save()

        # block 3b: check + process based on action

        this_event.action = line['Action']
        this_event.event_type = line['Event Type']

        if line['Action'] == 'Pull' or line['Action'] == 'PullOB':
            # if we start on defence - first event will be a pull
            this_pull = handle_new_pull(line['Hang Time (secs)'])
            this_point.pull_ID = this_pull.pull_ID

        # elif line['Action'] == 'D':

        # elif line['Action'] == 'Catch':

        # elif line['Action'] == 'Drop':

        # elif line['Action'] == 'Stall':

        this_event.save()

    csv_file.close()
    return 'SUCCESSFULLY REACHED END OF PARSE'


# handle_x functions always return the object they created/found


def handle_new_event(possession_ID,line):
    this_event = models.Event()
    this_event.action = line['Action']
    this_event.elapsedtime = line['Elapsed Time (secs)']

    this_event.save()
    return this_event


def handle_new_pull(hangtime=None):
    this_pull = models.Pull()
    if hangtime:
        this_pull.hangtime = hangtime

    this_pull.save()
    return this_pull


def handle_new_point(game_ID, line, halfatend=False):
    print('entering HNP')
    #print('line ='+str(line))
    print('gameid = '+str(game_ID))
    this_point = models.Point()
    this_point.game_ID = game_ID
    this_point.point_elapsed_seconds = line['Point Elapsed Seconds']
    this_point.startingfence = line['Line']
    this_point.ourscore_EOP = line['Our Score - End of Point']
    this_point.theirscore_EOP = line['Their Score - End of Point']
    this_point.halfatend = halfatend

    # pull will be set when we get to that event in block 2
    this_point.save()
    return this_point


def handle_new_possession(point_ID):
    this_possession = models.Possession()
    this_possession.point_ID = point_ID

    this_possession.save()
    return this_possession


def handle_check_player(player_pk):
    # check if a Player object for this player exists

    # get player by pk # TODO: there's a good django way to do this
    # if it doesn't exist - do something
    # should always exist if the pk exists

    for player in models.Player.objects.all():
        if player.player_ID == player_pk:
            return player
