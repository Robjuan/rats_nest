import logging
from django.db import models
from .managers import PossessionQuerySet, EventQuerySet, TeamQuerySet



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
    GENDER_CHOICES = (('M', 'Male'),
                      ('F', 'Female'))

    player_ID = models.AutoField(primary_key=True)

    # non-key
    proper_name = models.CharField(max_length=30)
    gender = models.CharField(max_length=1,
                              choices=GENDER_CHOICES)
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
        return str(self.proper_name) + ' [P id:' + str(self.player_ID) + ']'

    def add_if_not_blank_or_existing(self, attr, value):
        now = getattr(self, attr)

        if now and value not in now:
            new = now + ',' + value

        elif now and value in now:
            return None

        else:  # if not now
            new = value

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

    objects = TeamQuerySet.as_manager()

    class Meta:
        ordering = ('team_name',)

    def __str__(self):
        return 'Team - [id:' + str(self.team_ID) + '] ' + str(self.team_name)

    def has_games(self):  # to check if the team has games (row-level)
        return Game.objects.filter(team=self).exists()


class Game(models.Model):
    game_ID = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name='teams')
    # need to handle a way to save the opposing team name without creating too much junk
    # if we only know the name

    # SET_NULL means that if you delete the referenced team, this just goes to null
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
                             models.CASCADE,
                             related_name='points')

    players = models.ManyToManyField(Player,
                                     related_name='players_on_field')

    # non-key
    point_elapsed_seconds = models.IntegerField()
    startingfence = models.CharField(max_length=30)
    ourscore_EOP = models.IntegerField()  # EOP = end of point
    theirscore_EOP = models.IntegerField()
    halfatend = models.BooleanField(default=False)  # TODO (as required) - cessation events exist sometimes

    def __str__(self):
        return 'Point - [id:' + str(self.point_ID) + '] game: ' + str(self.game) + \
               ',[us|them]: [' + str(self.ourscore_EOP) + '|' + str(self.theirscore_EOP) + ']'

    # using pk to order here is fine except in case of multithreading / errors in parse
    # parse will create the points in turn

    def previous_point(self):
        return self.next_point(backwards=True)

    def next_point(self, backwards=False):

        logger = logging.getLogger(__name__)

        if backwards:
            target_int = int(self.point_ID) - 1
            loggerstr = 'no immediately previous point exists: '+str(self.point_ID)
        else:
            target_int = int(self.point_ID) + 1
            loggerstr = 'no immediately subsequent point exists: '+str(self.point_ID)

        try:
            ret_point = Point.objects.get(pk=target_int)

            if not ret_point.game == self.game:
                raise self.DoesNotExist

        except self.DoesNotExist:
            # logger.info(loggerstr)
            ret_point = None

        return ret_point


class Possession(models.Model):
    possession_ID = models.AutoField(primary_key=True)
    point = models.ForeignKey(Point, on_delete=models.CASCADE, related_name='possessions')
    # if the point is deleted, delete relevant possessions

    # manager
    objects = PossessionQuerySet.as_manager()

    def __str__(self):
        return 'Possession - [id:' + str(self.possession_ID) + ']'


class Event(models.Model):
    event_ID = models.AutoField(primary_key=True)
    # to find out the order of events in a possession, can sort by pk

    possession = models.ForeignKey(Possession,
                                   on_delete=models.CASCADE, related_name='events')

    # if events are related to the other team (blocks, throwaways, goals etc)
    # then all three of passer/receiver/defender will be blank or anonymous

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
        if self.is_opposition():
            return 'Opp Event '+str(self.event_ID)+'; action: '+str(self.action)
        elif self.passer and self.receiver:
            return 'Event '+str(self.event_ID)+'; p: '+str(self.passer)+'; r: '+str(self.receiver)+'; a: '+str(self.action)
        elif self.passer:
            return 'Event '+str(self.event_ID)+'; p: '+str(self.passer)+'; a: '+str(self.action)
        elif self.defender:
            return 'Event '+str(self.event_ID)+'; d: '+str(self.defender)+'; a: '+str(self.action)
        else:
            return 'Event '+str(self.event_ID)+'; action: '+str(self.action)

    # this will currently include breaks like cessation
    # those are not included in all() tho
    def is_opposition(self):
        if self.passer is None and self.receiver is None and self.defender is None:
            return True
        else:
            return False


class Pull(models.Model):
    pull_ID = models.AutoField(primary_key=True)
    # PROTECT will error if the player is deleted when pulls exist
    player = models.ForeignKey(Player,
                               on_delete=models.PROTECT,
                               null=True)  # anonymous pulls happen # TODO (lp) a way to still link these to the team
    point = models.ForeignKey(Point,
                              on_delete=models.CASCADE)

    # non-key
    hangtime = models.DecimalField(null=True,
                                   decimal_places=2,
                                   max_digits=4)

    def __str__(self):
        return 'Pull - [id:' + str(self.pull_ID) + '] player: ' + str(self.player)
