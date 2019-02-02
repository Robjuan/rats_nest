# this is where we write analyses
import logging


def get_all_analyses():
    import inspect, sys
    full_list = []
    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isfunction):
        if name == '__builtins__' or name == 'get_all_analyses':
            continue

        # can also do sorting here to only show complete packages and not helpers

        else:
            full_list.append((obj, name))

    return full_list
    # will return {name:func} for all top-level members (funcs, classes etc)
    # if we keep this file clear and only build analysis functions in it, should be sweet


# all top-level analysis functions will be handed game_id and team_id as kwargs
# these are the actual objects being passed in, not pks
# 'game' and 'team' are the kwargs

# TODO (current) follow these steps for analysis creation
# step 1: build out basic descriptive stats that we can use to build more complex stats
# step 2: combine those to get output
# step 3: build an output framework (table?)

def descriptive_team_analyis(*args, **kwargs):
    game = kwargs.pop('game')
    team = kwargs.pop('team')

    from .analysis_helpers import completions_by_player

    team_players = team.players.all()  # TODO (current) this isn't returning all relevant players?

    completion_list = []
    for player in team_players:
        completion_list.append((player.proper_name,completions_by_player(game,player)))

    return completion_list

def null_analysis(*args, **kwargs):
    game = kwargs.pop('game')
    team = kwargs.pop('team')

    return 'first null, team: ' + str(team)


def second_null_analysis(*args, **kwargs):
    game = kwargs.pop('game')
    team = kwargs.pop('team')

    # do even cooler shit

    return 'second null, game: ' + str(game)
