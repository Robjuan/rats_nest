# helpers.py
# contains short helper functions, usually used by views

import logging


def not_blank_or_anonymous(name):
    """
    Tests for empty string or string equates to Anonymous

    :param name: String
    :return: Bool
    """

    # 'Anonymous' is inserted by UA for "other team" stats, and Throwaways (as receiver)
    if name and name != 'Anonymous':
        return True
    else:
        if not name:
            logger = logging.getLogger(__name__)
            logger.debug('Blank name being filtered')
        return False


def fetch_match(csv_name):
    """
    Finds player object matching given csv_name, if exists

    :param csv_name: str used to represent player in UA csv
    :return: player object if match, else None
    """
    from .models import Player

    for stored_player in Player.objects.all():
        if csv_name in stored_player.csv_names or csv_name == stored_player.proper_name:
            return stored_player

    # only if no match found
    return None
