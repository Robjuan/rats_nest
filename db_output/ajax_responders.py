import logging
from django.http import JsonResponse


def set_extra_details(request):
    """
    used to display the details of the selected object in a secondary div

    :param request: POST containing a str modeltype and int selected_pk
    :return: json containing all info of the model instance with pk = selecte_pk
    """
    import json
    from .models import Player, Team

    logger = logging.getLogger(__name__)

    modeltype = request.POST['modeltype']
    selected_pk = request.POST['selected_pk']

    if modeltype == 'Player':
        obj = Player.objects.get(pk=selected_pk)
    elif modeltype == 'Team':
        obj = Team.objects.get(pk=selected_pk)
    else:
        logger.error('only Team and Player supported as modeltypes')
        return JsonResponse({'success': False})

    infodict = {}
    for field in obj._meta.fields:
        infodict[field.name] = str(getattr(obj, field.name))

    # does this json dump support datetime?
    # does this need to be stringified?
    infojson = json.dumps(infodict)

    return JsonResponse({'success': True,
                         'infojson': infojson})


def set_active_form(request):
    """
    keeps the django session up to date on which form is active in validation

    expects a jsonified dict called 'json_request_dict'

    :param request:
    :return:
    """
    import json
    from collections import OrderedDict
    logger = logging.getLogger(__name__)

    # fetch dict of forms (as indices) to update from jquery
    # (dict will most likely be one item long)
    try:
        request_dict = json.loads(request.POST['json_request_dict'])
    except KeyError:
        logger.error('"json_request_dict" not found in ajax request')
        return JsonResponse({'success': False})

    # get current session data or creat if required
    active_form_dict = request.session['active_form_dict'] or OrderedDict()

    # add all k:v pairs from request into current session data
    for key, value in request_dict.items():
        active_form_dict[key] = value

    request.session['active_form_dict'] = active_form_dict

    return JsonResponse({'success': True})


def get_initial_match(request):
    """
    gets match for any given match_key (if exists)
    expects 'match_key' in request.POST

    :param request:
    :return: json
    """
    logger = logging.getLogger(__name__)

    # check that the dict has been prepared by the view - fail gracefully if not
    if 'match_dict' not in request.session:
        logger.error('match_dict not found in session data')
        return JsonResponse({'success': False,
                             'warning': 'match_dict not found in session data'})

    match_dict = request.session['match_dict']

    # check our key against the dict
    try:
        match_id, match_text = match_dict[request.POST['match_key']]

    # KeyError is when no match exists
    # TypeError is when dict = None or empty
    except (KeyError, TypeError):
        match_id = False
        match_text = 'No match found'

    return JsonResponse({'success': True,
                         'match_text': match_text,
                         'match_id': match_id})
