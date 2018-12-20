from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Player)
admin.site.register(Team)
admin.site.register(Game)
admin.site.register(Pull)
admin.site.register(Point)
admin.site.register(Possession)
admin.site.register(Event)

admin.site.register(csvDocument)
