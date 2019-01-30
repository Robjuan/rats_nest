from django.urls import path

from . import views, simple_views

# path takes four args - route, view, *kwargs, *name
# route is a url pattern
# view is the view to call, httprequest as first arg rest as kwargs
# kwargs are optional


urlpatterns = [
    # Category: Parse
    path('parse_select', views.parse_select, name='parse_select'),
    path('parse_validate_player', views.parse_validate_player, name='parse_validate_player'),
    path('parse_verify', views.parse_verify, name='parse_verify'),
    path('parse_results', views.parse_results, name='parse_results'),

    # Category: Upload
    path('upload_csv', views.upload_csv, name='upload_csv'),

    # Category: Analysis
    path('analysis_select', views.analysis_select, name='analysis_select'),
    # path('analysis_present', views.analysis_present, name='analysis_present'),

    path('insert_test_data', simple_views.insert_test_data, name='insert_test_data'),

    path('contact_us', simple_views.contact_us, name='contact_us'),
    path('', simple_views.index, name='index'),
]