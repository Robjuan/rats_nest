# analysis_descriptive.py
# differs from analyis_helpers in that these return numbers/stats

from .analysis_helpers import *


def completion_pct_by_player(games, player, return_count=False, decimal_places=2):
    """
    calculates completion % for player over specified games

    :param games: at least one game to look at
    :param player: specific player to get completion % of
    :param return_count: def=False - if True, return also the total number of throws
    :param decimal_places: def=2 - dp to round completion % to
    :return: completion % for player over specified game(s)
    """

    from decimal import Decimal

    total_throws = 0
    total_throwaways = 0

    for game in games:

        game_events = get_events_by_game(game)

        this_game_throws = game_events.filter(passer=player)
        this_game_throwaways = game_events.filter(passer=player, action='Throwaway')

        total_throws += this_game_throws.count()
        total_throwaways += this_game_throwaways.count()

    if total_throws:
        completion = Decimal((total_throws - total_throwaways) / total_throws)*100
        completion = round(completion, decimal_places)
    else:
        completion = 0

    if return_count:  # TODO: is this pythonic
        return completion, total_throws
    else:
        return completion


def goals_by_player(games, player):

    total_goals = 0
    for game in games:
        game_events = get_events_by_game(game)
        this_game_goals = game_events.filter(receiver=player, action='Goal')
        total_goals += this_game_goals.count()

    return total_goals


def points_played_by_player(games, player):
    from .models import Point

    total_points = 0
    for game in games:
        this_game_points = Point.objects.filter(game=game)
        for point in this_game_points:
            if player in point.players.all():
                total_points += 1

    return total_points
