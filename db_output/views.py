from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse(render(request, 'db_output/index.html', {}))


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

    # print(Players.objects.all())

    return HttpResponse('done!')


def upload_csv(request):

    return HttpResponse('this is text')
