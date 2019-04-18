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
    please_confirm_delete = False

    if please_confirm_insert and settings.DEBUG:
        from .models import Player
        for player in Player.objects.filter(proper_name__icontains='test_Player'):
            number = player.proper_name.split('_')[2]
            if int(number) % 2 == 0:
                player.gender = 'F'
                player.save()

        text = 'inserted'

    elif please_confirm_delete and settings.DEBUG:
        from .models import csvDocument
        for i in range(1, 5):
            csvDocument.objects.filter(id=i).delete()
        text = 'deleted'

    else:
        text = 'Nothing to see here'

    return HttpResponse(text)
