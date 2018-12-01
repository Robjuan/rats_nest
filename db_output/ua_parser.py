# this is where the magic happens
# this file will parse UA-generated csv files and save them to models

from .models import *


def parse():
    from .models import csvDocument

    display_txt = []
    count = 0
    for obj in csvDocument.objects.all():  # objects.all pulls every record from the csvDocument table
        for line in obj.file:               # x.file pulls the value that x record in the file column, ie the csv
            display_txt.append(str(line))   # ready for reading like any local csv file :)
            count += 1
            if count > 10:
                break

    return display_txt
