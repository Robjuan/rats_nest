# in this file we will construct the dataframes required for higher level analysis
import pandas as pd
from .analysis_helpers import *
from .ua_definitions import *


def construct_game_dataframe(game):

    # points as index
    # each stat as a column
    # columns: passes, possessions, turnovers, blocks, starting_fence, we_scored
    # from read_frame: starting_fence, ourscore_EOP, theirscore_EOP
    # to be calculated: passes, possessions, turnovers, blocks, we_scored

    from .models import Point, Possession
    from django_pandas.io import read_frame

    logger = logging.getLogger(__name__)

    # TODO (now) need to be able to iterate over game.points
    # presently type(game.points) = RelatedManager

    df = read_frame(Point.objects.filter(game=game),
                    fieldnames=['startingfence', 'ourscore_EOP', 'theirscore_EOP'],
                    index_col='point_ID')

    # assign(colname=data) data must be a series or series-like object

    passes = pd.Series([get_events_by_point(point).filter(action__in=PASSES).count() for point in game.points],
                       index=df.index)
    df.assign(passes=passes)

    turnovers = pd.Series([get_events_by_point(point).filter(action__in=TURNOVERS) for point in game.points],
                          index=df.index)
    df.assign(turnovers=turnovers)

    blocks = pd.Series([get_events_by_point(point).filter(action='D').count() for point in game.points],
                       index=df.index)
    df.assign(blocks=blocks)

    possessions = pd.Series([point.possessions.count() for point in game.points],
                            index=df.index)
    df.assign(possessions=possessions)

    we_scored = pd.Series([point.next_point().ourscore_EOP > point.ourscore_EOP for point in game.points],
                          index=df.index)
    df.assign(we_scored=we_scored)

    logger.debug(df)
    return df
