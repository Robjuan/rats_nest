# this is where the magic happens
# this file will parse UA-generated csv files and save them to models

# at what points do we want to raise an exception? when would it crash the app if it gets unexpected input?

import csv
from . import models
import logging


def get_player_names(file_obj_pk):
    """
    mini-parse, to get nothing but all the csv_names in a file

    :param file_obj_pk: pk to csvdocument obj with file
    :return: list of player names in file
    """

    file = models.csvDocument.objects.get(pk=file_obj_pk).file
    csv_reader = csv.DictReader([line.decode('utf-8') for line in file.readlines()], delimiter=',')

    player_name_list = []
    for line in csv_reader:
        for x in range(0, 27):
            num = 'Player ' + str(x)
            if line[num] not in player_name_list:
                player_name_list.append(line[num])

    return player_name_list


def check_conversion_dict(conversion_dict, file_obj_pk):
    """
    Checks conversion_dict against player_names for consistency

    :param conversion_dict:
    :param file_obj_pk: to feed get_player_names
    :return: name if found to be not in conversion_dict, else True
    """
    import logging
    logger = logging.getLogger(__name__)

    player_names = get_player_names(file_obj_pk)
    for name in player_names:
        if not name:
            logger.warning('blank name in check_conversion_dict')
            continue
        if name not in conversion_dict:
            return name
    return True

# ** One per game columns:
# Date/Time
# Tournament
# Opponent
#
# ** One per point columns:
# Line (refers to starting fence)
# Our Score EOP
# Their Score EOP
# Point Elapsed Seconds
#
# ** One per possession columns:
# Players # this is tracked per-point but we know it should be per (possession or event?)
#         # we are storing this as per-event
#
#
# ** One per event columns:
# Event Type
# Action
# Passer
# Receiver
# Hang Time
# Elapsed Time (sec)


def parse(file_obj_pk, team_obj_pk, conversion_dict, verify=True, opposition_pk=None):
    """
    The parse function. Central logic of converting UA csv to database objects.

    :param file_obj_pk: pk of the file object to be parsed
    :param team_obj_pk: pk of the team object this game is about
    :param conversion_dict: dict in form {csv_name: pk} to convert raw data to pks for parse
    :param verify: should this game be marked as verified on completion, defaults True
    :param opposition_pk: pk of the opposing Team object
    :return: TODO: have parse return summary of everything saved to db
    """
    logger = logging.getLogger(__name__)

    try:
        csv_obj = models.csvDocument.objects.get(pk=file_obj_pk)
        filename = csv_obj.file.name
        csv_file = csv_obj.file
        csv_reader = csv.DictReader([line.decode('utf-8') for line in csv_file.readlines()], delimiter=',')
        # DictReader means that each line is a dictionary, with name:value determined by column name:column value

    except OSError as e:
        logger.error(str(e))
        return None

    if not check_conversion_dict(conversion_dict, file_obj_pk):
        return None

    # *** valid column names from ua csv are:
    # Date/Time,Tournamemnt,Opponent,Point Elapsed Seconds,Line,Our Score - End of Point,Their Score - End of Point,
    # Event Type,Action,Passer,Receiver,Defender,Hang Time (secs),Elapsed Time (secs),
    # Player 0,Player 1,Player 2,Player 3,Player 4,Player 5,Player 6,Player 7,Player 8,Player 9,Player 10,Player 11,
    # Player 12,Player 13,Player 14,Player 15,Player 16,Player 17,Player 18,Player 19,Player 20,Player 21,Player 22,
    # Player 23,Player 24,Player 25,Player 26,Player 27,
    #
    # *** below are unused
    # Begin Area,Begin X,Begin Y,End Area,End X,End Y,
    # Distance Unit of Measure,Absolute Distance,Lateral Distance,Toward Our Goal Distance

    indexed_lines = list(enumerate(csv_reader))  # i wonder if this is memory inefficient?
    # indexed_lines[index] returns (index,line) tuple

    for index, line in indexed_lines:

        # block 1: first time through initialisation

        if index == 0:
            this_game = models.Game()
            this_game.datetime = line['Date/Time']
            this_game.tournament_name = line['Tournamemnt']  # UA csv has typo in column name "Tournamemnt"
            this_game.file_model = models.csvDocument.objects.get(pk=file_obj_pk)
            this_game.team = models.Team.objects.get(pk=team_obj_pk)
            this_game.verified = verify
            this_game.save()

            # TODO (soon): combine stats - link by fk first
            if opposition_pk:
                this_game.opposing_team = models.Team.objects.get(pk=opposition_pk)

            this_point = handle_new_point(this_game.game_ID, line, conversion_dict)
            this_possession = handle_new_possession(this_point.point_ID)

        # block 2: checks for new point or new possession
        # should never be continuing in this block, or handling event-specific data
        # this block is for containers only

        if index > 0:  # first event will not require a new possession or point, those are already done
            # if either score has increased:
            points_completed = line['Our Score - End of Point'] + line['Their Score - End of Point']
            prev_points_completed = indexed_lines[index - 1][1]['Our Score - End of Point'] + \
                                    indexed_lines[index - 1][1]['Their Score - End of Point']

            if points_completed > prev_points_completed:
                this_point.save()
                this_possession.save()

                # will never be half at end of first point

                this_point = handle_new_point(this_game.game_ID, line, conversion_dict)
                this_possession = handle_new_possession(this_point.point_ID)

            elif line['Event Type'] != indexed_lines[index - 1][1]['Event Type']:  # new possession but not new point
                this_possession.save()

                this_possession = handle_new_possession(this_point.point_ID)

            else:
                pass  # neither new point nor new possession

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

        this_event = handle_new_event(this_possession.possession_ID, line)

        if line['Defender']:
            this_event.defender = handle_check_player(conversion_dict[line['Defender']])
        else:
            this_event.passer = handle_check_player(conversion_dict[line['Passer']])
            this_event.receiver = handle_check_player(conversion_dict[line['Receiver']])

        this_event.save()

        this_event.action = line['Action']
        this_event.event_type = line['Event Type']

        if line['Action'] == 'Pull' or line['Action'] == 'PullOB':
            # if we start on defence - first event will be a pull
            this_pull = handle_new_pull(conversion_dict[line['Defender']], this_point.point_ID,
                                        line['Hang Time (secs)'])

        # elif line['Action'] == 'D':

        # elif line['Action'] == 'Catch':

        # elif line['Action'] == 'Drop':

        # elif line['Action'] == 'Stall':

        this_event.save()

    this_game.save()
    csv_file.close()
    csv_obj.parsed = True
    csv_obj.save()
    return 'SUCCESSFULLY REACHED END OF PARSE'


# handle_x functions always return the object they created/found
def handle_check_player(player_pk):
    # check if a Player object for this player exists
    # return None if the "pk" for Anonymous is passed
    if player_pk == -1:  # Anonymous
        return None
    else:
        return models.Player.objects.get(pk=player_pk)


def handle_new_event(possession_ID, line):
    this_event = models.Event()
    this_event.action = line['Action']
    this_event.elapsedtime = line['Elapsed Time (secs)']
    this_event.possession = models.Possession.objects.get(pk=possession_ID)

    this_event.save()
    return this_event


def handle_new_pull(player_ID, point_ID, hangtime=None):
    this_pull = models.Pull()
    this_pull.player = handle_check_player(player_ID)
    this_pull.point = models.Point.objects.get(pk=point_ID)  # this assumes point will always exist before pull
    if hangtime:
        this_pull.hangtime = hangtime

    this_pull.save()
    return this_pull


def handle_new_point(game_ID, line, conversion_dict, halfatend=False):
    this_point = models.Point()
    this_point.game = models.Game.objects.get(pk=game_ID)
    this_point.point_elapsed_seconds = line['Point Elapsed Seconds']
    this_point.startingfence = line['Line']
    this_point.ourscore_EOP = line['Our Score - End of Point']
    this_point.theirscore_EOP = line['Their Score - End of Point']
    this_point.halfatend = halfatend
    this_point.save()

    # store players
    player_col_list = []
    for x in range(0, 27):
        col = 'Player ' + str(x)
        player_col_list.append(col)

    for player_col in player_col_list:
        if line[player_col]:
            player = handle_check_player(conversion_dict[line[player_col]])
            this_point.players.add(player)  # this is building the manytomany

    this_point.save()
    return this_point


def handle_new_possession(point_ID):
    this_possession = models.Possession()
    this_possession.point = models.Point.objects.get(pk=point_ID)

    this_possession.save()
    return this_possession

