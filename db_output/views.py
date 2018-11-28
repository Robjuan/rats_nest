from django.shortcuts import render
from django.http import HttpResponse

import os, psycopg2

def index(request):
    return HttpResponse("this is 'index' view of db_output <p> "
                        "if you didn't specify a url past /db_output/ you will come here")


def postgreSQL(request):

    from .models import Players

    display_txt = []
    for table in Players.objects.all():
        display_txt.append(str(table))

    return HttpResponse('this is produced by the DB:<p>' +
                        str(display_txt))

def insert_test_player(request):

    from .models import Players
    p = Players(proper_name='homer simpson', hometown='evergreen terrace')
    p.save()

    print(Players.objects.all())

    return HttpResponse('done!')
