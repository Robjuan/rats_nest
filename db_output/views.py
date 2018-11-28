from django.shortcuts import render
from django.http import HttpResponse

import os, psycopg2

def index(request):
    return HttpResponse("this is 'index' view of db_output <p> "
                        "if you didn't specify a url past /db_output/ you will come here")


def postgreSQL(request):
    
    DATABASE_URL = os.environ['DATABASE_URL']

    conn = psycopg2.connect(DATABASE_URL, sslmode='allow')
    # open cursor
    cur = conn.cursor()

    cur.execute("""SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'""")


    for table in cur.fetchall():
        print(table)

    return HttpResponse('this will become something produced by our DB')

def insert_test_player(request):

    print()

    from .models import Player
    p = Player(proper_name='homer simpson', hometown='evergreen terrace')
    p.save()

    print(Player.objects.all())

    return HttpResponse('done!')
