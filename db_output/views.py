from django.shortcuts import render
from django.http import HttpResponse

import os, psycopg2

# settings.py takes care of the backend of this

def index(request):
    return HttpResponse("this is 'index' view of db_output <p> "
                        "if you didn't specify a url past /db_output/ you will come here")


def db_view(request):
    # connect to DB
    DATABASE_URL = os.environ['DATABASE_URL']

    print()
    conn = psycopg2.connect(DATABASE_URL, sslmode='allow')
    # open cursor
    cur = conn.cursor()

    cur.execute("""SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'""")

    display_val = []

    for table in cur.fetchall():
        display_val.append(table)

    return HttpResponse('this will become something produced by our DB')


