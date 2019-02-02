# analysis_helpers.py
# this will hold all the smaller, descriptive stats functions that are called by top-level functions

# all should probably take in game

# https://docs.djangoproject.com/en/2.1/topics/db/queries/


def completions_by_player(game, player):
    from .models import Event

    throws = Event.objects.filter(passer=player)
    throwaways = Event.objects.filter(passer=player, action='Throwaway')

    if throws.count():
        completion = (throwaways.count() / throws.count())*100
    else:
        completion = None

    return completion
