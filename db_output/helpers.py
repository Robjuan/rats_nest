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


def breakdown_data_file(file):
    """
    Takes a csv data file with an arbitrary number of games,
    breaks them into single game files, with opposition name appended

    :param file: csv filename
    :return: list of tuples (new_content_file, new_filename, opponent, datetime)
    """
    import csv
    import linecache
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

