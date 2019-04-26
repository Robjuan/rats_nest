# helpers.py
# contains short helper functions, usually used by views

import logging


def generate_readable(instance):
    """
    generates a dict in form {fieldname: fieldvalue} for a given object instance

    :param instance: object to get readable form of
    :return: dict ready to be displayed
    """
    logger = logging.getLogger(__name__)

    disp_dict = {}
    for field in instance._meta.fields:

        # logger.debug(field.name)
        disp_dict[field.name] = str(getattr(instance, field.name))

    return disp_dict


def generate_active_form_dict(match_dict):
    """
    creates a dict based on enumeration
    order of match_dict should match that of formset
    keys of return dict will then match to formset form indices

    :param match_dict: OrderedDict of matches
    :return:
    """
    from collections import OrderedDict

    logger = logging.getLogger(__name__)

    if not isinstance(match_dict, OrderedDict):
        logger.debug('match_dict is not OrderedDict - ordering is assumed')

    active_form_dict = OrderedDict()
    for index, match in enumerate(match_dict.values()):
        # index here will match the form index
        if match[0]:  # match is tuple (pk, str) (pk = None if no match)
            active_form_dict[index] = 1  # primary active
        else:
            active_form_dict[index] = 2  # secondary active

    return active_form_dict


def get_best_match(model, name):
    """
    Finds object matching given name, used for validation

    :param name: str used to represent player in UA csv
    :param model: model to search (only Team and Player supported)
    :return: pk of player object if match, else None
    """
    from .models import Player, Team
    from difflib import get_close_matches

    logger = logging.getLogger(__name__)

    if model == Player:
        check1 = {}
        for player in Player.objects.filter(proper_name__istartswith=name):
            check1[player.proper_name] = player.player_ID
        check2 = {}
        for player in Player.objects.filter(csv_names__icontains=name):
            for csv_name in player.csv_names.split(','):
                check2[csv_name] = player.player_ID
        check_against = {}
        check_against.update(check1)
        check_against.update(check2)

    elif model == Team:
        check_against = {}
        for team in Team.objects.filter(team_name__icontains=name):
            check_against[team.team_name] = team.team_ID

    else:
        logger.error('only Player and Team are supported models for get_best_match')
        return None

    match = get_close_matches(name, list(check_against.keys()), n=1)
    if match:
        return check_against[match[0]]
    else:
        logger.info('no match found for '+str(name))
        return None


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


def breakdown_data_file(file):
    """
    Takes a csv data file with an arbitrary number of games,
    breaks them into single game files, with opposition name prepended

    :param file: csv filename
    :return: list of tuples (new_content_file, new_filename, opponent, datetime)
    """
    import csv
    from django.core.files.base import ContentFile

    logger = logging.getLogger(__name__)
    # decode out of bytes into string

    csv_reader = csv.DictReader([line.decode('utf-8') for line in file.readlines()])
    indexed_lines = list(csv_reader)

    file_list = []
    for i in range(0, len(indexed_lines)):
        if indexed_lines[i]['Date/Time'] != indexed_lines[i-1]['Date/Time'] or i == 0:

            # for filename
            opponent = indexed_lines[i]['Opponent']
            datetime = indexed_lines[i]['Date/Time']
            # create file
            new_filename = 'vs' + opponent + '_' + file.name
            new_content_file = ContentFile('')
            csv_writer = csv.writer(new_content_file)
            csv_writer.writerow(indexed_lines[i].keys())  # header row

            file_list.append((new_content_file, new_filename, opponent, datetime))

        csv_writer.writerow(indexed_lines[i].values())

    logger.info('Breaking file into '+str(len(file_list))+' sub files')
    return file_list
