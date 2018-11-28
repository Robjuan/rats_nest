from django.db import models

# todo: this should be Players
class Player(models.Model):
    player_ID = models.AutoField(primary_key=True)

    # non-key
    proper_name = models.CharField(max_length=30)
    hometown = models.CharField(max_length=30,
                                blank=True)
    position = models.CharField(max_length=30,
                                blank=True)


class Teams(models.Model):
    team_ID = models.AutoField(primary_key=True)
    players = models.ManyToManyField(Player)
    # ManyToMany doesn't take on_delete??
    # PROTECT will raise an error when the referenced obj (ie, the players?) are deleted
    # don't delete players if the team exists

    # non-key
    team_name = models.CharField(max_length=30)
    origin = models.CharField(max_length=30,
                              blank=True)
    division = models.CharField(max_length=30,
                                blank=True)


class Games(models.Model):
    game_ID = models.AutoField(primary_key=True)
    team_ID = models.ForeignKey(Teams,
                                on_delete=models.PROTECT)
    # need to handle a way to save the opposing team name without creating too much junk
    # if we only know the name

    # SET_NULL means that if you delete the referenced team, this just goes to null
    opposing_team_ID = models.ForeignKey(Teams,
                                         on_delete=models.SET_NULL,
                                         blank=True,
                                         null=True,
                                         related_name='opposition_id')
    opposing_game_ID = models.ForeignKey('self',
                                         on_delete=models.SET_NULL,
                                         blank=True,
                                         null=True,
                                         related_name='opposition_game_id')

    # non-key
    datetime = models.DateTimeField()
    tournament_name = models.CharField(max_length=30,
                                       blank=True)
    location = models.CharField(max_length=30,
                                blank=True)
    conditions = models.CharField(max_length=30,

                                  blank=True)


class Pulls(models.Model):
    pull_ID = models.AutoField(primary_key=True)
    # PROTECT will error if the player is deleted when pulls exist
    player_ID = models.ForeignKey(Player,
                                  on_delete=models.PROTECT)

    # non-key
    hangtime = models.DecimalField(null=True,
                                   decimal_places=2,
                                   max_digits=4)


class Points(models.Model):
    point_ID = models.AutoField(primary_key=True)
    # CASCADE means that if the game is deleted, all the relevant points will be deleted too
    game_ID = models.ForeignKey(Games,
                                models.CASCADE)
    # SET NULL means that if the pull is deleted, this just goes to null
    pull_ID = models.ForeignKey(Pulls,
                                on_delete=models.SET_NULL,
                                blank=True,
                                null=True)

    # non-key
    point_elapsed_seconds = models.IntegerField()
    startingfence = models.CharField(max_length=30) # not 100% settled on this
    ourscore_EOP = models.IntegerField() # EOP = end of point
    theirscore_EOP = models.IntegerField()
    halfatend = models.BooleanField(default=False)


class Possessions(models.Model):
    possession_ID = models.AutoField(primary_key=True)
    point_ID = models.ForeignKey(Points,
                                 on_delete=models.CASCADE)
    # if the point is deleted, delete relevant possessions


class PossessionEvents(models.Model):
    event_ID = models.AutoField(primary_key=True)
    possession_ID = models.ForeignKey(Possessions,
                                      on_delete=models.CASCADE)
    players = models.ManyToManyField(Player,
                                     related_name='players_onfield')
    # if the possession is deleted, delete relevant events
    passer = models.ForeignKey(Player,
                               on_delete=models.PROTECT,
                               blank=True,
                               related_name='passer')
    receiver = models.ForeignKey(Player,
                                 on_delete=models.PROTECT,
                                 blank=True,
                                 related_name='receiver')
    defender = models.ForeignKey(Player,
                                 on_delete=models.PROTECT,
                                 blank=True,
                                 related_name='defender')
    # don't allow deletion of players if they have events attached to them
    # depending on the event_type, either:
    # defender ONLY will be blank, or passer&recevier will BOTH be blank

    event_type = models.CharField(max_length=30)
    elapsedtime = models.IntegerField()

