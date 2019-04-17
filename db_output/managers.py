# managers.py
# this stores our custom QuerySets and Managers for ez filtering
# https://docs.djangoproject.com/en/2.1/topics/db/managers/#creating-a-manager-with-queryset-methods
# https://stackoverflow.com/questions/29798125/when-should-i-use-a-custom-manager-versus-a-custom-queryset-in-django

# USAGE:
# Models.objects.custom_function()
# eg
# Team.objects.with_games()


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


class TeamQuerySet(models.QuerySet):
    def with_games(self):
        ret_ids = []
        for team in self.all():
            if team.has_games():
                ret_ids.append(team.team_ID)

        return self.filter(pk__in=ret_ids)

