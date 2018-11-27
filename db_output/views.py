from django.shortcuts import render

from django.http import HttpResponse


def index(request):
    return HttpResponse("this is 'index' view of db_output")


