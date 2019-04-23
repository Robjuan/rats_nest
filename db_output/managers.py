# managers.py
# this stores our custom QuerySets and Managers for ez filtering
# https://docs.djangoproject.com/en/2.1/topics/db/managers/#creating-a-manager-with-queryset-methods
# https://stackoverflow.com/questions/29798125/when-should-i-use-a-custom-manager-versus-a-custom-queryset-in-django

# USAGE:
# Models.objects.custom_function()
# eg
# Team.objects.with_games()


from django.db import models
from .ua_definitions import *


class PossessionQuerySet(models.QuerySet):
    def no_cessation(self):
        ret_ids = []
        for poss in self.all():
            if not poss.events.filter(event_type__in=BREAK_TYPES).exists():
                ret_ids.append(poss.possession_ID)
        return self.filter(pk__in=ret_ids)


class EventQuerySet(models.QuerySet):
    def no_cessation(self):
        return self.exclude(event_type__in=BREAK_TYPES)

    def no_opposition_events(self):
        return self.filter(pk__in=[event.pk for event in self.all() if not event.is_opposition])


class TeamQuerySet(models.QuerySet):
    def with_games(self):
        ret_ids = []
        for team in self.all():
            if team.has_games():
                ret_ids.append(team.team_ID)

        return self.filter(pk__in=ret_ids)

