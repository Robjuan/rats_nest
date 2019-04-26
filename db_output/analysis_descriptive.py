# analysis_descriptive.py
# differs from analyis_helpers in that these return numbers/stats

from .analysis_helpers import *
import pandas as pd

# for each of these functions
# should return a series where the index is game


def throws_by_player(games, player):
    """
    builds a dataframe for a player representing their throws/turns across games

    dataframe in form:

    # (index) throws turns
    # <game>  x      y
    # <game2> x      y

    :param games:
    :param player:
    :return: pandas dataframe
    """

    logger = logging.getLogger(__name__)

    throw_dict = {}
    turn_dict = {}
    for game in games:
        game_events = get_events_by_game(game)
        throw_dict[game.game_ID] = game_events.filter(passer=player).count()
        turn_dict[game.game_ID] = game_events.filter(passer=player, action='Throwaway').count()

    d = {'throws': pd.Series(throw_dict), 'turns': pd.Series(turn_dict)}
    s_out = pd.DataFrame(d)

    #logger.debug(s_out)

    return s_out


def completion_pct_by_player(games, player, return_count=False, decimal_places=2):
    """
    calculates completion % for player over specified games

    :param games: at least one game to look at
    :param player: specific player to get completion % of
    :param return_count: def=False - if True, return also the total number of throws
    :param decimal_places: def=2 - dp to round completion % to
    :return: completion % for player over specified game(s)
    """

    total_throws = 0
    total_throwaways = 0

    for game in games:

        game_events = get_events_by_game(game)

        this_game_throws = game_events.filter(passer=player)
        this_game_throwaways = game_events.filter(passer=player, action='Throwaway')

        total_throws += this_game_throws.count()
        total_throwaways += this_game_throwaways.count()

    if total_throws:
        completion = float((total_throws - total_throwaways) / total_throws)*100
        completion = round(completion, decimal_places)
    else:
        completion = 0

    if return_count:  # is this pythonic
        return completion, total_throws
    else:
        return completion


def action_count_by_player(games, player, action):
    """
    gets a count of how many times player recorded a certain action across given games

    :param games:
    :param player:
    :param action: see ua_definitions
    :return:
    """
    logger = logging.getLogger(__name__)
    from .ua_definitions import RECEIVING_ACTIONS

    total_actions = 0
    for game in games:
        game_events = get_events_by_game(game)
        if action in RECEIVING_ACTIONS:
            this_game_actions = game_events.filter(receiver=player, action=action)
        else:
            logger.error('unsupported action: '+str(action)+'; returning 0')
            return 0

        total_actions += this_game_actions.count()

    return total_actions


def points_played_by_player(games, player, starting_fence=None):
    """
    Returns number of points played for a given player in given games.
    Filterable for all points, offense points or defense points.

    :param games:
    :param player:
    :param starting_fence: None, 'O' / 'Offense' or 'D' / 'Defense'
    :return: int number of points
    """

    from .models import Point

    logger = logging.getLogger(__name__)

    total_points = 0
    for game in games:
        if starting_fence == 'O' or starting_fence == 'Offense':
            this_game_points = Point.objects.filter(game=game, startingfence='O')
        elif starting_fence == 'D' or starting_fence == 'Defense':
            this_game_points = Point.objects.filter(game=game, startingfence='D')
        else:
            if starting_fence:
                logger.error('unsupported starting_fence: '+starting_fence+', returning all points')
            this_game_points = Point.objects.filter(game=game)

        for point in this_game_points:
            if player in point.players.all():
                total_points += 1

    return total_points
