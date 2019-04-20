# simple_views.py
# contains simple views with little/no processing

import logging
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings


def index(request):
    logger = logging.getLogger(__name__)
    logger.info('index.html accessed')
    return HttpResponse(render(request, 'db_output/index.html', {}))


def contact_us(request):
    return HttpResponse(render(request, 'db_output/contact_us.html', {}))


def insert_test_data(request):
    # PLEASE BE VERY CAREFUL WITH MANUAL ADDITION AND SUBTRACTION
    # Use the Admin portal for one offs

    please_confirm_insert = False
    please_confirm_move = False

    if please_confirm_insert and settings.DEBUG:
        from .models import Player
        for player in Player.objects.filter(proper_name__icontains='test_Player'):
            number = player.proper_name.split('_')[2]
            if int(number) % 2 == 0:
                player.gender = 'F'
                player.save()

        text = 'inserted'

    elif please_confirm_move and settings.DEBUG:
        from .models import csvDocument
        import os

        for file_obj in csvDocument.objects.filter(parsed=True):
            head, tail = os.path.split(file_obj.file.name)

            archive_path = os.path.join('csv', '.archive', tail)
            manual_path = os.path.join('csv', '.manually_handled', tail)

            try_archive = os.path.join(settings.MEDIA_ROOT, archive_path)
            try_manual = os.path.join(settings.MEDIA_ROOT, manual_path)

            if os.path.isfile(try_archive):
                file_obj.file.name = archive_path

            elif os.path.isfile(try_manual):
                file_obj.file.name = manual_path

            file_obj.save()

        text = 'moved files'

    else:
        text = 'Nothing to see here'

    return HttpResponse(text)
