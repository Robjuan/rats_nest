# analysis_helpers.py
# these return querysets for further processing

# https://docs.djangoproject.com/en/2.1/topics/db/queries/

import logging


def get_dataframe_columns(frame, extra=[], start=0):
    game_columns = frame.columns.values.tolist()

    for index, extra_col in enumerate(extra, start=start):
        game_columns.insert(index, extra_col)

    return game_columns


def starting_fence_flip(starting_fence):
    if starting_fence == 'D':
        return 'O'
    elif starting_fence == 'O':
        return 'D'


def bool_we_scored(point):
    if point.previous_point():
        return point.ourscore_EOP > point.previous_point().ourscore_EOP
    else:
        return bool(point.ourscore_EOP)


def get_events_by_game(game):
    """
    returns all events for a game
    REMOVES CESSATIONS

    :param game: obj
    :return: qs
    """
    from .models import Event

    all_pks = []

    for point in game.points.all():
        for possession in point.possessions.no_cessation():
            for event in possession.events.no_cessation():
                all_pks.append(event.pk)

    all_events = Event.objects.filter(pk__in=all_pks)

    return all_events


# TODO ( as needed ) move opposition events to a manager check
def get_events_by_point(point, opposition_events=1):
    """
    returns a queryset of events that came from a given point
    opposition_events can be 0, 1, 2
    0 - include no opposition events
    1 - include all events (default)
    2 - include ONLY opposition events

    REMOVES CESSATIONS

    :param point:
    :param opposition_events: def True, include opposition events
    :return:
    """
    logger = logging.getLogger(__name__)

    from .models import Event

    ret_pks = []

    for possession in point.possessions.no_cessation().all():
        for event in possession.events.no_cessation().all():
            if opposition_events == 1:
                ret_pks.append(event.event_ID)
            if opposition_events == 2 and event.is_opposition():
                ret_pks.append(event.event_ID)
            if opposition_events == 0 and not event.is_opposition():
                ret_pks.append(event.event_ID)

    ret_events = Event.objects.filter(pk__in=ret_pks)
    return ret_events
