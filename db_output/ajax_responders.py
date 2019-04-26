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

    try:
        modeltype = request.POST['modeltype']
        selected_pk = request.POST['selected_pk']
    except KeyError:
        logger.error('modeltype/selected_pk not in request.POST')
        return JsonResponse({'success': False})

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


def get_datatables_json(request):
    """
    returns json constructed by team or game dataframe constuctor

    expects in POST:
     'target_constructor' ('Team' or 'Game')
     'data_reference' (game_id (int) if Game, [game_ids] (list of ints) if Team)
    :param request:
    :return:
    """
    from .analysis_constructors import construct_team_dataframe, construct_game_dataframe
    from .models import Game, Point
    from collections import OrderedDict
    import json
    import pandas as pd

    logger = logging.getLogger(__name__)

    try:
        target_constructor = request.POST['target_constructor']
        data_reference = json.loads(request.POST['data_reference'])
        columns = json.loads(request.POST['col_list'])
    except KeyError:
        logger.error('malformed data from jquery, returning failure')
        return JsonResponse({'success': False})

    # TODO (optim) caching? saving in session?

    if target_constructor == 'Team':
        game_dict = OrderedDict()
        for game_id in data_reference:
            game_id = int(game_id)
            try:
                game_frame = pd.read_json(request.session[game_id])
            except KeyError:
                logger.debug('df for game '+str(game_id)+' not found in session, recalculating')
                game_frame = construct_game_dataframe(Game.objects.get(pk=game_id))
                request.session[game_id] = game_frame.to_json()

            game_dict[game_id] = game_frame
        dataframe = construct_team_dataframe(game_dict)

    elif target_constructor == 'Game':
        try:
            dataframe = pd.read_json(request.session[data_reference])
        except KeyError:
            logger.debug('df for game ' + str(data_reference) + ' not found in session, recalculating')
            dataframe = construct_game_dataframe(Game.objects.get(pk=data_reference))
            request.session[data_reference] = dataframe.to_json()

    else:
        logger.error('invalid target_constructor passed: '+str(target_constructor))
        return JsonResponse({'success': False})

    extra_cols = []
    df_cols = dataframe.columns
    if len(columns) > len(df_cols):
        extra_cols = [c for c in columns if c not in df_cols.to_list()]

    records = len(dataframe.index)
    datatables_frame = dataframe.to_dict(orient='index')
    # {index -> {column -> value}}

    row_list = []
    i = 0
    for index, pair in datatables_frame.items():
        for col in extra_cols:
            # TODO: is defining column title logic here a good move?
            if col == 'Point':
                try:
                    obj = Point.objects.get(pk=index)
                    datatables_frame[index][col] = obj.point_ID
                except Point.DoesNotExist:
                    datatables_frame[index][col] = 'point_ID NF'
            elif col == 'Game':
                try:
                    obj = Game.objects.get(pk=index)
                    if obj.opposing_team:
                        datatables_frame[index][col] = 'vs ' + str(obj.opposing_team.team_name)
                    else:
                        datatables_frame[index][col] = '@ ' + str(obj.datetime)
                except Game.DoesNotExist:
                    datatables_frame[index][col] = 'game_ID NF'

            else:
                datatables_frame[index][col] = 'unsupported'
                logger.error('unsupported column listed in template')

        row_dict = datatables_frame[index]
        row_dict['DT_RowId'] = 'row_'+str(i)
        row_list.append(row_dict)
        i += 1

    #logger.debug(row_list)

    return JsonResponse({'success': True,
                         'draw': 1,
                         'recordsTotal': records,
                         'recordsFiltered': records,
                         'data': row_list})
