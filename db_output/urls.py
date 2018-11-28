from django.urls import path

from . import views

# path takes four args - route, view, *kwargs, *name
# route is a url pattern
# view is the view to call, httprequest as first arg rest as kwargs
# kwargs are optional



urlpatterns = [
    path('postgreSQL', views.db_view, name='postgreSQL'),
    path('', views.index, name='index')
    # empty route catches every request
]