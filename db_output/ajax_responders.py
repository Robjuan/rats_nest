import logging
from django.http import JsonResponse


def get_initial_match(request):
    """
    called only by ajax - validation_jquery.js
    FOR USE WITH FORMSETS ONLY

    :param request:
    :return: json
    """

    # check that the dict has been prepared by the view
    if 'match_dict' in request.session:
        match_dict = request.session['match_dict']
    else:
        return JsonResponse({'success': False})

    # check that the key given to us by ajax works
    if request.POST['match_key'] in match_dict:
        match_id, match_text = match_dict[request.POST['match_key']]
    else:
        return JsonResponse({'success': False})

    return JsonResponse({'success': True,
                         'match_text': match_text,
                         'match_id': match_id})


def update_details(request):
    """
    called only by ajax - validation_jquery.js

    :param request:
    :return: json
    """
    from django.apps import apps
    import json

    logger = logging.getLogger(__name__)

    form_class_string = request.POST['form_class']
    selected_pk = request.POST['selection_data']

    # make the selected_pk available to the view function
    request.session['selected_pk'] = selected_pk

    field_dict = json.loads(request.POST['json_field_dict'])

    # field dict is { field_id : field_name }
    # where field_id is the fully formed object id
    # and field_name is the corresponding field in the model

    form_class = apps.get_model('db_output', form_class_string)
    selected_object = form_class.objects.get(pk=selected_pk)

    field_data = {}
    for field_id, field_name in field_dict.items():
        if hasattr(selected_object, field_name):
            field_data[field_id] = getattr(selected_object, field_name)
        else:
            logger.warning(str(selected_object) + ' has no attr ' + str(field_name) + ', failing ajax.')
            return JsonResponse({'success': False})

    # field data is dict { field_id : value }
    # where field_id is the (fully formed) object id
    # and data is the val to set

    return JsonResponse({'field_data': field_data,
                         'success': True})
