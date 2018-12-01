from django.urls import path

from . import views

# path takes four args - route, view, *kwargs, *name
# route is a url pattern
# view is the view to call, httprequest as first arg rest as kwargs
# kwargs are optional



urlpatterns = [
    path('upload_csv', views.upload_csv, name='upload_csv'),
    path('test_output', views.test_output, name='test_output'),
    path('insert_test_data', views.insert_test_data, name='insert_test_data'),
    path('', views.index, name='index')
    # empty route catches every request ?
]