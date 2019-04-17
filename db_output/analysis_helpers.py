# analysis_helpers.py
# these return querysets for further processing

# https://docs.djangoproject.com/en/2.1/topics/db/queries/

import logging

# TODO (soon) replace these loops with searches across relationships
# TODO genericise

def get_events_by_game(game):
    from .models import Point, Possession, Event

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


def get_events_by_point(point, opposition_events=True):
    from .models import Possession, Event

    ret_pks = []

    for possession in Possession.objects.filter(point=point):
        for event in Event.objects.filter(possession=possession):
            if opposition_events:
                ret_pks.append(event.pk)
            else:
                if not event.is_opposition():
                    ret_pks.append(event.pk)

    ret_events = Event.objects.filter(pk__in=ret_pks)
    return ret_events
