# in this file we will define the different column sets, and function handlers to make sense of them
import logging

# these are all rows included in the default dataframe, and a title column


DEFAULT_TEAM_COLUMNS = ['Game', 'score', 'passes', 'completion_pct', 'possessions', 'score_pct', 'blocks',
                        'turns', 'block_pct', 'opp_turns', 'opp_poss']

DEFAULT_GAME_COLUMNS = ['Point', 'startingfence', 'ourscore_EOP', 'theirscore_EOP', 'we_scored', 'goals',
                        'passes', 'turnovers', 'blocks', 'possessions', 'callahans',
                        'opp_goals', 'opp_turns', 'opp_poss', 'opp_callahans'],

_playergame_columns = ['passes', 'catches', 'assists', 'goals', 'turnovers', 'blocks',
                      'atr', 'score_pct', 'block_pct']

DEFAULT_PLAYER_GAME_COLUMNS = ['Point'] + _playergame_columns

DEFAULT_PLAYER_TOTAL_COLUMNS = ['Player'] + _playergame_columns

# create new row layouts here, select which one to use in views.py
# TODO: make this selectable by end user

COMPACT_GAME_COLUMNS = ['Point', 'EOP Score', 'goals', 'startingfence',
                        'passes', 'turnovers', 'blocks', 'possessions', 'callahans',
                        'opp_goals', 'opp_turns', 'opp_poss', 'opp_callahans']


def handle_custom_row(col, index, data_dict):
    """
    takes in a custom column, (as well as row index and current row data)
    returns a value for that column (in that row)

    Note: this incoming dataframe could be any kind of dataframe

    :param col:  str colname
    :param index:  row index from dataframe
    :param data_dict: {column -> value} from dataframe
    :return: value to set in column
    """
    from .models import Game, Point, Player

    logger = logging.getLogger(__name__)

    # eventually if many custom columns get added, this fuction might become way too big
    # potentially a better way to do this whole thing

    # Point title column for game datatables
    if col == 'Point':
        try:
            obj = Point.objects.get(pk=index)
            return obj.point_ID
        except Point.DoesNotExist:
            return 'point_ID NF'

    # Game title column for team datatables
    elif col == 'Game':
        try:
            obj = Game.objects.get(pk=index)
            if obj.opposing_team:
                return 'vs ' + str(obj.opposing_team.team_name)
            else:
                return '@ ' + str(obj.datetime)
        except Game.DoesNotExist:
            return 'game_ID NF'

    # Score column for game datatables
    elif col == 'EOP Score':
        return str(data_dict['theirscore_EOP']) + ' - ' + str(data_dict['ourscore_EOP'])

    # player name title column for player totals dataframes
    elif col == 'Player':
        try:
            obj = Player.objects.get(pk=index)
            return obj.proper_name
        except Player.DoesNotExist:
            return 'player_ID NF'

    else:
        logger.error('unsupported col listed: '+str(col))
        return 'unsupported'

