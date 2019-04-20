# in this file we will construct the dataframes required for higher level analysis
import pandas as pd
from .analysis_helpers import *
from .ua_definitions import *


def construct_game_dataframe(game):
    """
    constructs game dataframe from game model
    points as index
    columns:
    startingfence (O/D), ourscore_EOP, theirscore_EOP, passes, turnovers, blocks, possessions, we_scored (bool)

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

    df = read_frame(Point.objects.filter(game=game),
                    fieldnames=['startingfence', 'ourscore_EOP', 'theirscore_EOP'],
                    index_col='point_ID')

    # assign(colname=data) ; data must be a series or series-like object

    passes = pd.Series([get_events_by_point(point).filter(action__in=PASSES).count() for point in game.points.all()],
                       index=df.index)
    df = df.assign(passes=passes)

    turnovers = pd.Series([get_events_by_point(point).filter(action__in=TURNOVERS).count() for point in game.points.all()],
                          index=df.index)
    df = df.assign(turnovers=turnovers)

    blocks = pd.Series([get_events_by_point(point).filter(action='D').count() for point in game.points.all()],
                       index=df.index)
    df = df.assign(blocks=blocks)

    possessions = pd.Series([point.possessions.count() for point in game.points.all()],
                            index=df.index)
    df = df.assign(possessions=possessions)

    we_scored = pd.Series([bool_we_scored(point) for point in game.points.all()],
                          index=df.index)
    df = df.assign(we_scored=we_scored)

    logger.debug(df)
    return df


def construct_team_dataframe(game_dict):
    """
    constructs the team_stats dataframe
    games as index
    columns: score, passes, completion%, blocks, block%, possessions, OP%

    :param game_dict: { game_id : game_dataframe }
    :return: team_dataframe
    """


    team_frame = pd.DataFrame(index=game_dict.keys())



    return team_frame
