# analysis_helpers.py
# these return querysets for further processing

# https://docs.djangoproject.com/en/2.1/topics/db/queries/


def get_events_by_game(game):
    from .models import Point, Possession, Event

    # TODO (db): this is slow and many loops - would chaining filters better be better?

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


def get_players_by_point(point):
    from .models import Possession, Event, Player

    point_players_ids = []

    possessions = Possession.objects.filter(point=point)
    for possession in possessions:
        events = Event.objects.filter(possession=possession)
        for event in events:
            for player in event.players:
                if player.player_ID not in point_players_ids:
                    point_players_ids.append(player.player_ID)

    point_players = Player.objects.filter(pk__in=point_players_ids)

    return point_players
