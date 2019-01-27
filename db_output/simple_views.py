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
        from .models import Player, Team
        p = Player(proper_name='Anonymous', hometown='San Francisco, CA', csv_names='Anonymous')
        p.save()

        t = Team(team_name='Default_team', origin='San Francisco, CA', division='Mixed')
        t.save()
        text = 'You have inserted:' + str(p) + ' and ' + str(t)

    elif please_confirm_delete and settings.DEBUG:
        from .models import csvDocument
        for i in range(1, 5):
            csvDocument.objects.filter(id=i).delete()
        text = 'deleted'

    else:
        text = 'Nothing to see here'

    return HttpResponse(text)
