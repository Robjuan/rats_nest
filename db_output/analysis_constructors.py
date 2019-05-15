# in this file we will construct the dataframes required for higher level analysis
import pandas as pd
from .analysis_helpers import *
from .ua_definitions import *


def prepare_rowlist_display(dataframe, columns):
    """
    takes in a database and a list of columns that we want to display

    generates a list that can be pumped straight into datatables
    each row is a dict in form: {index -> {column -> value}}

    :param dataframe: df
    :param columns: list of column names
    :return: list of rows
    """
    from .analysis_columns import handle_custom_row

    logger = logging.getLogger(__name__)

    df_cols = dataframe.columns
    extra_cols = [c for c in columns if c not in df_cols.to_list()]

    datatables_frame = dataframe.to_dict(orient='index')
    # {index -> {column -> value}}

    row_list = []
    i = 0
    for index, data_dict in datatables_frame.items():  # for each row
        row_dict = datatables_frame[index]

        for col in extra_cols:
            logger.debug('handling custom row: '+str(col)+'['+str(index)+']')
            row_dict[col] = handle_custom_row(col, index, data_dict)

        row_dict['DT_RowId'] = 'row_'+str(i)
        row_list.append(row_dict)
        i += 1

    return row_list


def construct_game_dataframe(game):
    """
    constructs game dataframe from game model
    points as index
    columns:
    startingfence (O/D), ourscore_EOP, theirscore_EOP, passes, turnovers, blocks, possessions, opp_poss, we_scored (bool)

    :param game: game instance
    :return: game dataframe
    """

    # points as index
    # each stat as a column
    # columns: passes, possessions, turnovers, blocks, starting_fence, we_scored
    # from read_frame: starting_fence, ourscore_EOP, theirscore_EOP
    # to be calculated: passes, possessions, turnovers, blocks, we_scored

    from .models import Point, Possession
    from django_pandas.io import read_frame

    logger = logging.getLogger(__name__)

    game_points = game.points.all().order_by('point_ID')

    # generate initial dataframe with some columns
    df = read_frame(game_points,
                    fieldnames=['startingfence', 'ourscore_EOP', 'theirscore_EOP'],
                    index_col='point_ID')

    # assign(colname=data) ; data must be a series or series-like object

    # bool - did we score this point
    we_scored = pd.Series([bool_we_scored(point) for point in game_points],
                          index=df.index)

    # goals we scored
    goals = pd.Series([get_events_by_point(point, opposition_events=0).filter(action__in=GOALS).count() for point in game_points],
                      index=df.index)

    # goals they scored
    opp_goals = pd.Series([get_events_by_point(point, opposition_events=2).filter(action__in=GOALS).count() for point in game_points],
                          index=df.index)

    # callahans we threw
    callahans_thrown = pd.Series([get_events_by_point(point, opposition_events=0).filter(action__in=CALLAHANS).count() for point in game_points],
                                 index=df.index)

    # callahans we caught
    opp_callahans_thrown = pd.Series([get_events_by_point(point, opposition_events=2).filter(action__in=CALLAHANS).count() for point in game_points],
                                 index=df.index)

    # number of passes we made
    passes = pd.Series([get_events_by_point(point, opposition_events=0).filter(action__in=PASSES).count() for point in game_points],
                       index=df.index)

    # number of TOTAL possessions
    total_possessions = pd.Series([point.possessions.no_cessation().all().count() for point in game_points],
                                  index=df.index)

    # number of turnovers we had
    turnovers = pd.Series([get_events_by_point(point, opposition_events=0).filter(action__in=TURNOVERS).count() for point in game_points],
                          index=df.index)

    # blocks we had
    blocks = pd.Series([get_events_by_point(point, opposition_events=0).filter(action__in=BLOCKS).count() for point in game_points],
                       index=df.index)

    # turnovers opponent had
    opp_turns = pd.Series([get_events_by_point(point, opposition_events=2).filter(action__in=TURNOVERS).count() for point in game_points],
                          index=df.index)

    # our possessions end on:
    # our goals + their blocks + our turnovers + their callahans scored (ours thrown)
    # in our stats, their blocks are not recorded only our turnovers
    possessions = goals + turnovers + callahans_thrown

    # their possessions end on:
    # their goals + our blocks + their turnovers + our callahans scored
    opp_possessions = opp_goals + blocks + opp_turns + opp_callahans_thrown

    # check our possession calculations
    pos_testframe = pd.concat([total_possessions - (possessions + opp_possessions)], axis=1)
    zeroframe = pd.DataFrame(0, index=pos_testframe.index, columns=pos_testframe.columns)
    if not zeroframe.equals(pos_testframe):
        logger.critical('error in possession calculation, below should be all zeros')
        logger.critical(pos_testframe)

    df = df.assign(we_scored=we_scored)
    df = df.assign(goals=goals)
    df = df.assign(passes=passes)
    df = df.assign(turnovers=turnovers)
    df = df.assign(blocks=blocks)
    df = df.assign(possessions=possessions)
    df = df.assign(callahans=opp_callahans_thrown)

    df = df.assign(opp_goals=opp_goals)
    df = df.assign(opp_turns=opp_turns)
    df = df.assign(opp_poss=opp_possessions)
    df = df.assign(opp_callahans=callahans_thrown)

    return df


def construct_team_dataframe(game_dict):
    """
    constructs the team_stats dataframe
    games as index
    columns: score, passes, completion%, blocks, block%, possessions, OP%

    :param game_dict: { game_id : game_dataframe }
    :return: team_dataframe
    """
    from .models import Game

    logger = logging.getLogger(__name__)

    # WHEN NOT SPECIFIED ALL STATS RELATE TO US ONLY

    # create list of 'vs opponent' row titles to use as index
    # indexlist = [str('vs ' + game.opposing_team.team_name) if game.opposing_team else game.game_ID for game in Game.objects.filter(pk__in=game_dict.keys())]

    indexlist = [game.game_ID for game in Game.objects.filter(pk__in=game_dict.keys())]

    tf = pd.DataFrame(index=indexlist)

    # final score of each game
    scores = [str(frame.iloc[-1]['ourscore_EOP']) + '-' + str(frame.iloc[-1]['theirscore_EOP']) for gameid, frame in game_dict.items()]
    score = pd.Series(scores, index=tf.index)

    # total passes per game
    passes = [frame['passes'].sum() for gameid, frame in game_dict.items()]
    passes = pd.Series(passes, index=tf.index)

    # turnovers we had
    turnovers = [frame['turnovers'].sum() for gameid, frame in game_dict.items()]
    t_series = pd.Series(turnovers, index=tf.index)

    completion = []
    for g_pass, g_turn in zip(passes, turnovers):
        if g_pass:
            comp_pct = round((g_pass - g_turn) / g_pass, 2)*100
        else:
            comp_pct = None

        completion.append(comp_pct)
    # completion %
    completion = pd.Series(completion, index=tf.index)

    # total possessions we had
    possessions = pd.Series([frame['possessions'].sum() for gameid, frame in game_dict.items()], index=tf.index)

    # turnovers our opponent committed
    opp_turns = pd.Series([frame['opp_turns'].sum() for gameid, frame in game_dict.items()], index=tf.index)

    # % of our possessions we scored on
    # ( goals / our_possessions ) * 100%
    goals = [frame.iloc[-1]['ourscore_EOP'] for gameid, frame in game_dict.items()]
    goals = pd.Series(goals, index=tf.index)
    score_pct = round((goals / possessions) * 100, 2)

    # number of possessions our opponents had
    opp_poss = [frame['opp_poss'].sum() for gameid, frame in game_dict.items()]
    opp_poss = pd.Series(opp_poss, index=tf.index)

    # number of blocks we got
    blocks = [frame['blocks'].sum() for gameid, frame in game_dict.items()]
    blocks = pd.Series(blocks, index=tf.index)

    # % of our opponents possessions where we got a block
    # ( blocks / opp_possessions ) * 100%
    block_pct = round((blocks / opp_poss) * 100, 2)

    tf = tf.assign(score=score)
    tf = tf.assign(passes=passes)
    tf = tf.assign(completion_pct=completion)
    tf = tf.assign(possessions=possessions)
    tf = tf.assign(score_pct=score_pct)
    tf = tf.assign(blocks=blocks)

    tf = tf.assign(turns=t_series)
    tf = tf.assign(opp_turns=opp_turns)
    tf = tf.assign(opp_poss=opp_poss)

    tf = tf.assign(block_pct=block_pct)

    return tf


def construct_player_totals_dataframe(game_dict):

    df = pd.concat([frame.sum() for gameid, frame in game_dict.items()], axis=1)

    return df


def construct_player_game_dataframe(player, game):
    """
    we want to know:
    passes thrown, catches, assists, goals, turnovers, blocks
    scoring reception %
    completion %
    assist : turnover ratio

    :param player:
    :param game:
    :return:
    """
    from .analysis_helpers import get_points_by_player

    logger = logging.getLogger(__name__)

    # todo: this is currently returning an empty queryset if the player didn't play any points
    # we are not handling this properly
    active_points = get_points_by_player(game, player)


    df = pd.DataFrame(index=[p.point_ID for p in active_points])

    passes = [get_events_by_point(point).filter(action__in=PASSES).filter(passer=player).count() for point in active_points]
    passes = pd.Series(passes, index=df.index)

    catches = [get_events_by_point(point).filter(action__in=CATCHES).filter(receiver=player).count() for point in active_points]
    catches = pd.Series(catches, index=df.index)

    assists = [get_events_by_point(point).filter(action__in=GOALS).filter(passer=player).count() for point in active_points]
    assists = pd.Series(assists, index=df.index)

    goals = [get_events_by_point(point).filter(action__in=GOALS).filter(receiver=player).count() for point in active_points]
    goals = pd.Series(goals, index=df.index)

    turnovers = [get_events_by_point(point).filter(action__in=TURNOVERS).filter(passer=player).count() for point in active_points]
    turnovers = pd.Series(turnovers, index=df.index)

    blocks = [get_events_by_point(point).filter(action__in=BLOCKS).filter(defender=player).count() for point in active_points]
    blocks = pd.Series(blocks, index=df.index)

    completion_pct = round(((passes - turnovers) / passes * 100), 2)
    score_pct = round((goals / catches * 100), 2)

    atr = round((assists / turnovers), 2)

    df = df.assign(passes=passes)
    df = df.assign(catches=catches)
    df = df.assign(assists=assists)
    df = df.assign(goals=goals)
    df = df.assign(turnovers=turnovers)
    df = df.assign(blocks=blocks)
    df = df.assign(score_pct=score_pct)
    df = df.assign(completion_pct=completion_pct)
    df = df.assign(atr=atr)

    logger.debug('pg df : '+str(df))

    return df
