from django.urls import path

from . import views, simple_views, ajax_responders

# path takes four args - route, view, *kwargs, *name
# route is a url pattern
# view is the view to call, httprequest as first arg rest as kwargs
# kwargs are optional

# TODO (soon): control manual access by URL


urlpatterns = [
    # jquery ajax
    # path('ajax/update_details', ajax_responders.update_details, name='ajax_update_details'),
    path('ajax/get_initial_match', ajax_responders.get_initial_match, name='ajax_get_initial_match'),
    path('ajax/set_active_form', ajax_responders.set_active_form, name='ajax_set_active_form'),
    path('ajax/set_extra_details', ajax_responders.set_extra_details, name='ajax_set_extra_details'),
    path('ajax/get_datatables_json', ajax_responders.get_datatables_json, name='ajax_get_datatables_json'),

    # Category: Parse
    path('parse_select', views.parse_select, name='parse_select'),
    path('parse_validate_team', views.parse_validate_team, name='parse_validate_team'),
    path('parse_validate_opposition', views.parse_validate_opposition, name='parse_validate_opposition'),
    path('parse_validate_player', views.parse_validate_player, name='parse_validate_player'),
    path('parse_verify', views.parse_verify, name='parse_verify'),
    path('parse_results', views.parse_results, name='parse_results'),

    # Category: Upload
    path('upload_csv', views.upload_csv, name='upload_csv'),

    # Category: Analysis
    path('analysis_select', views.analysis_select, name='analysis_select'),
    # path('analysis_present', views.analysis_present, name='analysis_present'),
    path('team_stats', views.team_stats, name='team_stats'),
    path('player_stats', views.player_stats, name='player_stats'),

    # Category: Simple & Other
    path('insert_test_data', simple_views.insert_test_data, name='insert_test_data'),

    path('contact_us', simple_views.contact_us, name='contact_us'),
    path('', simple_views.index, name='index'),
]