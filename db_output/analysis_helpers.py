# analysis_helpers.py
# these return querysets for further processing

# https://docs.djangoproject.com/en/2.1/topics/db/queries/

import logging


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