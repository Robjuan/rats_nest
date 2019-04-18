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
        logger.warning('match_dict is not OrderedDict - ordering is assumed')

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
    from django.db.models import Q

    logger = logging.getLogger(__name__)

    if model == Player:
        matches = Player.objects.filter(Q(proper_name__istartswith=name) | Q(csv_names__icontains=name)).order_by('player_ID')
    elif model == Team:
        matches = Team.objects.filter(team_name__icontains=name).order_by('team_ID')
    else:
        logger.warning('only Player and Team are supported models for get_best_match')
        return None

    # TODO (lp): more accurate similarity test than "first"
    if matches.first():
        return matches.first().pk
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
    breaks them into single game files, with opposition name appended

    :param file: csv filename
    :return: list of tuples (new_content_file, new_filename, opponent, datetime)
    """
    import csv
    from django.core.files.base import ContentFile

    # TODO: build test for this

    logger = logging.getLogger(__name__)
    # decode out of bytes into string

    csv_reader = csv.DictReader([line.decode('utf-8') for line in file.readlines()])
    indexed_lines = list(enumerate(csv_reader))
    # indexed_lines[index] returns (index, line) tuple

    file_list = []
    start_index = 0
    for index, line in indexed_lines:
        if index == 0:
            continue
        if line['Date/Time'] != indexed_lines[index-1][1]['Date/Time']:
            # index will always be line number - 1

            # logger.debug('prev: '+str(indexed_lines[index-1][1]['Opponent']))
            # logger.debug('curr: '+str(line['Opponent']))

            end_index = index

            opponent = indexed_lines[index-1][1]['Opponent']
            datetime = indexed_lines[index-1][1]['Date/Time']

            new_filename = opponent + '_' + file.name
            new_content_file = ContentFile('')
            csv_writer = csv.writer(new_content_file)
            csv_writer.writerow(indexed_lines[index][1].keys())  # header row

            # logger.debug('si' + str(start_index) + ',ei' + str(end_index))

            for i in range(start_index, end_index):
                csv_writer.writerow(indexed_lines[i][1].values())

            file_list.append((new_content_file, new_filename, opponent, datetime))

            start_index = index

    logger.info('Breaking file into '+str(len(file_list))+' sub files')
    return file_list
