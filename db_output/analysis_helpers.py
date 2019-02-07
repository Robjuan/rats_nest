# analysis_helpers.py
# this will hold all the smaller, descriptive stats functions that are called by top-level functions

# all should probably take in game

# https://docs.djangoproject.com/en/2.1/topics/db/queries/


def get_events_by_game(game):
    from .models import Point, Possession, Event

    # TODO (soon/db): this is slow and many loops - chaining filters better would be better

    all_pks = []

    points = Point.objects.filter(game=game)
    for point in points:
        possessions = Possession.objects.filter(point=point)
        for possession in possessions:
            events = Event.objects.filter(possession=possession)
            for event in events:
                all_pks.append(event.pk)

    all_events = Event.objects.filter(pk__in=all_pks)

    return all_events


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

    if return_count:
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
    from .models import Point, Possession, Event

    # players are stored per-event
    # how to get for point? - add half point if subbed
    # should we be storing per possession

    # TODO (current): how can we search upwards through the structure without always looping

    total_points = 0
    found = False
    for game in games:
        this_game_points = Point.objects.filter(game=game)
        for point in this_game_points:
            this_point_possessions = Possession.objects.filter(point=point)
            for possession in this_point_possessions:
                this_possession_events = Event.objects.filter(possession=possession)
                for event in this_possession_events:
                    if player in event.players.all():
                        total_points += 1
                        found = True  # if you find a player in an event, break out until you reach the next point
                        break
                if found:
                    break
            if found:
                found = False
                break

    return total_points
