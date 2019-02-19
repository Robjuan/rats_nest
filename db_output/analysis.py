# this is where we write analyses
import logging


def get_all_analyses():
    import inspect, sys
    logger = logging.getLogger(__name__)
    full_list = []
    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isfunction):
        if name == '__builtins__' or name == 'get_all_analyses':
            continue

        else:
            full_list.append((obj, name))

    return full_list
    # will return {func:name} for all top-level members (funcs, classes etc)
    # if we keep this file clear and only build analysis functions in it, should be sweet


# all top-level analysis functions will be handed game_id and team_id as kwargs
# these are the actual objects being passed in, not pks
# 'game' and 'team' are the kwargs

# can store basic box stats for display for completed (ie, AUL 2018) seasons etc

# we can redefine these as classes and thereby set cute label names etc
# calling the "analysisclass.analyse()" in view


# step 1: build out basic descriptive stats that we can use to build more complex stats
# step 2: combine those to get output
# step 3: build an output framework (table?)

def descriptive_offence_team_analysis(*args, **kwargs):
    """
    Generates basic descriptive stats for all players on a team given certain games

    :param args:
    :param kwargs:
    :return:
    """
    games = kwargs.pop('games')
    team = kwargs.pop('team')
    logger = logging.getLogger(__name__)

    from .analysis_descriptive import completion_pct_by_player, goals_by_player, points_played_by_player

    decimal_places = 2

    team_players = team.players.all()
    # first row is header row
    stat_list = [('Player Name', 'Goals', 'Completion %', 'Throws Attempted', 'Points Played')]
    for player in team_players:
        pct, throwcount = completion_pct_by_player(games, player, return_count=True, decimal_places=decimal_places)
        goals = goals_by_player(games, player)
        pp = points_played_by_player(games, player)
        stat_list.append((player.proper_name, goals, pct, throwcount, pp))

    cum_goals = 0
    cum_throws = 0
    cum_turns = 0
    for stat_row in stat_list:
        if isinstance(stat_row[1], str):  # skip header row
            continue
        print(stat_row)
        cum_goals += stat_row[1]
        cum_throws += stat_row[3]
        cum_turns += (stat_row[2]/100)*stat_row[3]

    cum_pct = round((cum_turns / cum_throws) * 100, decimal_places)

    stat_list.append(('Cumulatively', cum_goals, cum_pct, cum_throws, 'n/a'))

    return stat_list, 'table'


def placeholder_analytic_possession_analysis(*args, **kwargs):
    """
    To calculate efficiency and effectiveness per-possession for a team across given games

    :param args:
    :param kwargs:
    :return:
    """
    games = kwargs.pop('games')
    team = kwargs.pop('team')

    # # OFFENCE
    # - effectiveness: likelihood of a goal being scored on particular possession
    # - efficiency: goals scored per resource spent
    # -- resources: passes
    # likelihood of next pass being scoring pass
    # likelihood of next pass being turnover
    # passes per possession (ends in goal)
    # passes per possession (non-scoring (turnover or
    # possessions per goal (lower the better)
    # Recovery %: pct time disc recovered after offensive turn



    # # DEFENCE
    # blocks per break

    for game in games:
        pass

    return 'first null, team: ' + str(team), 'list'


def null_analysis(*args, **kwargs):
    games = kwargs.pop('games')
    team = kwargs.pop('team')

    return 'first null, team: ' + str(team), 'list'


def second_null_analysis(*args, **kwargs):
    games = kwargs.pop('games')
    team = kwargs.pop('team')

    # do even cooler shit

    return 'second null, game: ' + str(games), 'list'
