# this is where we write analyses
import logging


def get_all_analyses():
    import inspect, sys
    full_list = []
    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isfunction):
        if name == '__builtins__' or name == 'get_all_analyses':
            continue
        else:
            full_list.append((obj, name))

    return full_list
    # will return {name:func} for all top-level members (funcs, classes etc)
    # if we keep this file clear and only build analysis functions in it, should be sweet

# all analysis functions will be handed game_id and team_id as kwargs
# these are the actual objects being passed in not pks


def null_analysis(*args, **kwargs):
    game = kwargs.pop('game')
    team = kwargs.pop('team')

    # do cool shit

    return 'first null, team: ' + str(team)


def second_null_analysis(*args, **kwargs):
    game = kwargs.pop('game')
    team = kwargs.pop('team')

    # do even cooler shit

    return 'second null, game: ' + str(game)
