from django.db import models


# document upload - not for stats analysis

class csvDocument(models.Model):
    your_team_name = models.CharField(max_length=30)
    description = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='csv/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'csv from '+str(self.your_team_name)+', uploaded at: '+str(self.uploaded_at)[:19] # cut off secs

# statistic storage


class Player(models.Model):
    player_ID = models.AutoField(primary_key=True)

    # non-key
    proper_name = models.CharField(max_length=30)
    hometown = models.CharField(max_length=30,
                                blank=True)
    position = models.CharField(max_length=30,
                                blank=True)

    nickname = models.CharField(max_length=255,
                                blank=True)

    csv_names = models.CharField(max_length=255,
                                 blank=True)  # comma separated values in a string

    def __str__(self):
        return 'Player - [id:'+str(self.player_ID)+'] '+str(self.proper_name)


class Team(models.Model):
    team_ID = models.AutoField(primary_key=True)
    players = models.ManyToManyField(Player)
    # ManyToMany doesn't take on_delete??

    # non-key
    team_name = models.CharField(max_length=30)
    origin = models.CharField(max_length=30,
                              blank=True)
    division = models.CharField(max_length=30,
                                blank=True)

    def __str__(self):
        return 'Team - [id:'+str(self.team_ID)+'] '+str(self.team_name)


class Game(models.Model):
    game_ID = models.AutoField(primary_key=True)
    team_ID = models.ForeignKey(Team,
                                on_delete=models.PROTECT)
    # need to handle a way to save the opposing team name without creating too much junk
    # if we only know the name

    # SET_NULL means that if you delete the referenced team, this just goes to null
    opposing_team_ID = models.ForeignKey(Team,
                                         on_delete=models.SET_NULL,
                                         blank=True,
                                         null=True,
                                         related_name='opposition_id')
    opposing_game_ID = models.ForeignKey('self',
                                         on_delete=models.SET_NULL,
                                         blank=True,
                                         null=True,
                                         related_name='opposition_game_id')

    file_model = models.ForeignKey(csvDocument,
                                   on_delete=models.PROTECT)

    # non-key
    datetime = models.DateTimeField()
    tournament_name = models.CharField(max_length=30,
                                       blank=True)
    location = models.CharField(max_length=30,
                                blank=True)
    conditions = models.CharField(max_length=30,
                                  blank=True)

    def __str__(self):
        return 'Game - [id:'+str(self.game_ID)+'] '+str(self.datetime)



class Pull(models.Model):
    pull_ID = models.AutoField(primary_key=True)
    # PROTECT will error if the player is deleted when pulls exist
    player_ID = models.ForeignKey(Player,
                                  on_delete=models.PROTECT)

    # non-key
    hangtime = models.DecimalField(null=True,
                                   decimal_places=2,
                                   max_digits=4)

    def __str__(self):
        return 'Pull - [id:' + str(self.pull_ID) + '] player_id:' + str(self.player_ID)


class Point(models.Model):
    point_ID = models.AutoField(primary_key=True)
    # CASCADE means that if the game is deleted, all the relevant points will be deleted too
    game_ID = models.ForeignKey(Game,
                                models.CASCADE)
    # SET NULL means that if the pull is deleted, this just goes to null
    pull_ID = models.ForeignKey(Pull,
                                on_delete=models.SET_NULL,
                                blank=True,
                                null=True)

    # non-key
    point_elapsed_seconds = models.IntegerField()
    startingfence = models.CharField(max_length=30) # not 100% settled on this
    ourscore_EOP = models.IntegerField()  # EOP = end of point
    theirscore_EOP = models.IntegerField()
    halfatend = models.BooleanField(default=False)

    def __str__(self):
        return 'Point - [id:'+str(self.point_ID)+'] game:'+str(self.game_ID) +\
               ',[us|them]: ['+str(self.ourscore_EOP)+'|'+str(self.theirscore_EOP)+']'


class Possession(models.Model):
    possession_ID = models.AutoField(primary_key=True)
    point_ID = models.ForeignKey(Point,
                                 on_delete=models.CASCADE)
    # if the point is deleted, delete relevant possessions

    def __str__(self):
        return 'Possession - [id:'+str(self.possession_ID)+']'


class Event(models.Model):
    event_ID = models.AutoField(primary_key=True)
    possession_ID = models.ForeignKey(Possession,
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

    def __str__(self):
        return 'Event - [id:'+str(self.event_ID)+']'
