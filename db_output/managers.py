# managers.py
# this stores our custom QuerySets and Managers for ez filtering
# https://docs.djangoproject.com/en/2.1/topics/db/managers/#creating-a-manager-with-queryset-methods

from django.db import models


class PointQuerySet(models.QuerySet):
    def by_game(self, game):
        return self.filter(game=game)


class PossessionQuerySet(models.QuerySet):
    def by_point(self, point):
        return self.filter(point=point)


class EventQuerySet(models.QuerySet):
    def by_possession(self, possession):
        return self.filter(possession=possession)


class TeamManager(models.Manager):
    def get_queryset(self):
        initial = super().get_queryset()
        ret_ids = []
        for team in initial:
            if team.has_games():
                ret_ids.append(team.team_ID)

        return initial.filter(pk__in=ret_ids)
