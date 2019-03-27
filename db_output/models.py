from django.db import models
from .managers import PointQuerySet, PossessionQuerySet, EventQuerySet


# document upload - not for stats analysis

class csvDocument(models.Model):
    your_team_name = models.CharField(max_length=30)
    description = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='csv/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    season = models.IntegerField()

    parsed = models.BooleanField(null=True)

    def __str__(self):
        return 'csv: ' + str(self.your_team_name) + ', uploaded: ' + str(self.uploaded_at)[5:19] + ', filename: ' + \
               str(self.file.name)


# statistic storage

class Player(models.Model):
    player_ID = models.AutoField(primary_key=True)

    # non-key
    proper_name = models.CharField(max_length=30)

    dob = models.DateField(max_length=8,
                           blank=True,
                           null=True)
    hometown = models.CharField(max_length=30,
                                blank=True)
    position = models.CharField(max_length=30,
                                blank=True)
    nickname = models.CharField(max_length=255,
                                blank=True)
    numbers = models.CharField(max_length=255,
                               blank=True)
    csv_names = models.CharField(max_length=255,
                                 blank=True)  # comma separated values in a string

    class Meta:
        ordering = ('proper_name',)

    def __str__(self):
        return str(self.proper_name) + ' [P id: ' + str(self.player_ID) + ']'

    def add_if_not_blank_or_existing(self, attr, value):
        now = getattr(self, attr)
        if now and value not in now:
            new = now + ',' + value
        else:
            new = now
        setattr(self, attr, new)


class Team(models.Model):
    DIVISION_CHOICES = (
        ('W', "Womens"),
        ('M', "Mens / Opens"),
        ('X', "Mixed")
    )
    team_ID = models.AutoField(primary_key=True)
    players = models.ManyToManyField(Player)
    # ManyToMany doesn't take on_delete

    # non-key
    team_name = models.CharField(max_length=30)
    origin = models.CharField(max_length=30,
                              blank=True)
    gender_division = models.CharField(max_length=30,
                                       choices=DIVISION_CHOICES)

    age_division = models.CharField(max_length=30,
                                    blank=True,
                                    null=True)

    class Meta:
        ordering = ('team_name',)

    def __str__(self):
        return 'Team - [id:' + str(self.team_ID) + '] ' + str(self.team_name)


class Game(models.Model):
    game_ID = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='this_team')
    # need to handle a way to save the opposing team name without creating too much junk
    # if we only know the name

    # SET_NULL means that if you delete the referenced team, this just goes to null
    # TODO (now): get opposing team info going so we can show you who the game is against
    opposing_team = models.ForeignKey(Team,
                                      on_delete=models.SET_NULL,
                                      blank=True,
                                      null=True,
                                      related_name='opposition')
    opposing_game = models.ForeignKey('self',
                                      on_delete=models.SET_NULL,
                                      blank=True,
                                      null=True,
                                      related_name='opposition_game')

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
    notes = models.CharField(max_length=255,
                             blank=True)

    # verification is just an extra flag for us to show what is legit data - will mostly be on
    verified = models.BooleanField()

    class Meta:
        ordering = ('datetime',)

    def __str__(self):
        if self.opposing_team:
            return '[G '+str(self.game_ID)+']: ' +\
                   str(self.team.team_name) + ' vs ' + str(self.opposing_team.team_name) +\
                   ' @ ' + str(self.tournament_name)

        else:
            return '[G '+str(self.game_ID)+']: ' + str(self.team.team_name) + ' @ ' + str(self.tournament_name) +\
                   ' @ ' + str(self.datetime)[:19]


class Point(models.Model):
    point_ID = models.AutoField(primary_key=True)
    # CASCADE means that if the game is deleted, all the relevant points will be deleted too
    game = models.ForeignKey(Game,
                             models.CASCADE)

    players = models.ManyToManyField(Player,
                                     related_name='players_on_field')

    # non-key
    point_elapsed_seconds = models.IntegerField()
    startingfence = models.CharField(max_length=30)  # not 100% settled on this
    ourscore_EOP = models.IntegerField()  # EOP = end of point
    theirscore_EOP = models.IntegerField()
    halfatend = models.BooleanField(default=False)

    # manager
    objects = PointQuerySet.as_manager()

    def __str__(self):
        return 'Point - [id:' + str(self.point_ID) + '] game:' + str(self.game) + \
               ',[us|them]: [' + str(self.ourscore_EOP) + '|' + str(self.theirscore_EOP) + ']'


class Possession(models.Model):
    possession_ID = models.AutoField(primary_key=True)
    point = models.ForeignKey(Point, on_delete=models.CASCADE)
    # if the point is deleted, delete relevant possessions

    # manager
    objects = PossessionQuerySet.as_manager()

    def __str__(self):
        return 'Possession - [id:' + str(self.possession_ID) + ']'


class Event(models.Model):
    event_ID = models.AutoField(primary_key=True)
    # to find out the order of events in a possession, can sort by pk

    possession = models.ForeignKey(Possession,
                                   on_delete=models.CASCADE)

    # if the possession is deleted, delete relevant events
    passer = models.ForeignKey(Player,
                               on_delete=models.PROTECT,
                               blank=True,
                               null=True,
                               related_name='passer')
    receiver = models.ForeignKey(Player,
                                 on_delete=models.PROTECT,
                                 blank=True,
                                 null=True,
                                 related_name='receiver')
    defender = models.ForeignKey(Player,
                                 on_delete=models.PROTECT,
                                 blank=True,
                                 null=True,
                                 related_name='defender')
    # don't allow deletion of players if they have events attached to them
    event_type = models.CharField(max_length=30)
    action = models.CharField(max_length=30)
    elapsedtime = models.IntegerField()

    # manager
    objects = EventQuerySet.as_manager()

    def __str__(self):
        return 'Event - [id:' + str(self.event_ID) + ']'


class Pull(models.Model):
    pull_ID = models.AutoField(primary_key=True)
    # PROTECT will error if the player is deleted when pulls exist
    player = models.ForeignKey(Player,
                               on_delete=models.PROTECT)
    point = models.ForeignKey(Point,
                              on_delete=models.CASCADE)

    # non-key
    hangtime = models.DecimalField(null=True,
                                   decimal_places=2,
                                   max_digits=4)

    def __str__(self):
        return 'Pull - [id:' + str(self.pull_ID) + '] player:' + str(self.player)
