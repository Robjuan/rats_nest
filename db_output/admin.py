from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Players)
admin.site.register(Teams)
admin.site.register(Games)
admin.site.register(Pulls)
admin.site.register(Points)
admin.site.register(Possessions)
admin.site.register(PossessionEvents)

admin.site.register(csvDocument)