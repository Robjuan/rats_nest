import logging
import pandas as pd


def get_all_analyses():
    """
    returns {func:name} for all top-level members (funcs, classes etc)
    excepting this function, and 'constructors_test'
    this is for specific analysis selection (analysis_select)

    :return:
    """
    import inspect, sys
    logger = logging.getLogger(__name__)
    full_list = []
    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isfunction):
        if name == '__builtins__' or name == 'get_all_analyses' or name == 'constructors_test':
            continue

        else:
            full_list.append((obj, name))

    return full_list
    # if we keep this file clear and only build analysis functions in it, should be sweet


def constructors_test(*args, **kwargs):
    """
    base function for team_stats

    :param kwargs: games , team from data selection
    :return: team_dataframe
    """
    from .analysis_constructors import construct_game_dataframe, construct_team_dataframe
    from collections import OrderedDict

    games = kwargs.pop('games')
    team = kwargs.pop('team')

    game_dict = OrderedDict()
    for game in games:
        game_frame = construct_game_dataframe(game)
        game_dict[game.game_ID] = game_frame

    ret_frame = construct_team_dataframe(game_dict)

    return ret_frame.to_html()


def pandas_test_analysis(*args, **kwargs):
    from .analysis_descriptive import throws_by_player, points_played_by_player
    from .models import Player
    games = kwargs.pop('games')
    team = kwargs.pop('team')
    logger = logging.getLogger(__name__)

    # only inspect actions by players with at least one point played across all games being analysed
    active_ids = []
    for player in team.players.all():
        if points_played_by_player(games, player):
            active_ids.append(player.player_ID)
    active_players = Player.objects.filter(pk__in=active_ids)

    # list of series objects, one per player
    series = [throws_by_player(games, player) for player in active_players.all()]

    ret_frame = pd.concat(series, keys=[player.player_ID for player in active_players.all()])
    ret_frame.index.rename(['player', 'game'], inplace=True)
    # this is creating a hierarchical index where player is level 0, game is level 1

    logger.debug(ret_frame)
    return ret_frame.to_html(), 'raw'


def descriptive_offense_team_analysis(*args, **kwargs):
    """
    Generates basic descriptive stats for all players on a team given certain games

    :param args:
    :param kwargs:
    :return:
    """
    games = kwargs.pop('games')
    team = kwargs.pop('team')
    logger = logging.getLogger(__name__)

    from .analysis_descriptive import completion_pct_by_player, action_count_by_player, points_played_by_player

    decimal_places = 2

    team_players = team.players.all()
    # first row is header row
    stat_list = [('Player Name', 'Goals', 'Completion %', 'Throws Attempted', 'Points Played')]
    for player in team_players:
        pct, throwcount = completion_pct_by_player(games, player, return_count=True, decimal_places=decimal_places)
        goals = action_count_by_player(games, player, action='Goal')
        pp = points_played_by_player(games, player)
        stat_list.append((player.proper_name, goals, pct, throwcount, pp))

    cum_goals = 0
    cum_throws = 0
    cum_turns = 0
    for stat_row in stat_list:
        if isinstance(stat_row[1], str):  # skip header row
            continue
        cum_goals += stat_row[1]
        cum_throws += stat_row[3]
        cum_turns += (stat_row[2]/100)*stat_row[3]

    cum_pct = round((cum_turns / cum_throws) * 100, decimal_places)
    # this will throw an exception if your team did not have a single throw

    stat_list.append(('Cumulatively', cum_goals, cum_pct, cum_throws, 'n/a'))

    return stat_list, 'table'


def team_efficiency(*args, **kwargs):
    from .models import Point, Possession, Event

    games = kwargs.pop('games')
    team = kwargs.pop('team')

    # passes per goal (including the assist)

    output_data = [('Game', 'Passes', 'Goals')]

    for game in games:
        if game.opposing_team:
            intro = "Against " + str(game.opposing_team)
        else:
            intro = "In game " + str(game)

        # todo: replace this loop with a complex query
        for point in Point.objects.filter(game=game):
            point_events_pks = []
            passes = 0
            goals = 0
            for possession in Possession.objects.filter(point=point):
                for event in Event.objects.filter(possession=possession):
                    point_events_pks.append(event.event_ID)

            point_events = Event.objects.filter(pk__in=point_events_pks)
            if point_events.last().event_type == 'Defense':  # we got scored on
                continue
            else:  # we scored
                for event in point_events:
                    if (event.action == 'Catch' or event.action == 'Goal') and (event.event_type == 'Offense'):
                        passes += 1
                    if event.action == 'Goal' and event.event_type == 'Offense':
                        goals += 1

                output_data.append((intro, passes, goals))
                # not summing these at all

    return output_data, 'table'


def placeholder_analysis(*args, **kwargs):
    """
    dreams go here

    """
    games = kwargs.pop('games')
    team = kwargs.pop('team')

    # Offensive Rating - Goals per 100 possessions
    # likelihood of scoring or turnover per pass in point (graph)
    # % of offensive possessions we score
    # % of offensive possessions recovered after TO (recovery)

    # % of defensive possessions we get a block
    # % of offensive possessions we score after getting a block (conversion)

    return 'placeholder analysis - keep dreaming'
