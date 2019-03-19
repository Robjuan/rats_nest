# views.py
# contains the logic for presenting all non-trivial pages on the site

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.conf import settings
import logging

# TODO (lp) refactor the logic out of views into it's own file ('view_logic.py')
# each view should then be only dealing with form creation / rendering / data getting etc
# pass what it gets from the form into a couple of functions, get info
# then test!!!


def upload_csv(request):
    """
    Handles logic for upload_csv page
    Uses "upload_csv" for itself, redirects to "parse_select" on success

    Category: Upload
    :param request: django object
    :return: response object
    """
    from .forms import csvDocumentForm
    from .models import csvDocument
    from .helpers import breakdown_data_file

    # TODO (feat): take in more information about the game (location, conditions etc)
    # use tags for conditions

    # this permission check might be duplicative as it is also checked in the template
    # TODO: this permission doesn't actually exist, but rob_development is a superuser so has_perm always returns True
    # so is rats_development

    if request.method == 'POST' and request.user.has_perm('db_output.can_upload_csv'):
        form = csvDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            written_data = form.cleaned_data
            file_list = breakdown_data_file(request.FILES['file'])
            for content_file, filename, opponent, datetime in file_list:
                this_description = written_data['description'] + '_' + str(opponent)

                # TODO: check we're not saving/parsing the same game (datetime, tournament name)
                this_model = csvDocument(your_team_name=written_data['your_team_name'],
                                         season=written_data['season'],
                                         description=this_description,
                                         file=content_file,
                                         parsed=False)
                this_model.file.save(filename, content_file, save=True)  # calls models.save() immediately

            return HttpResponseRedirect('parse_select')
    else:
        form = csvDocumentForm()
        return render(request, 'db_output/upload_csv.html', {'form': form})


def parse_select(request):
    """
    Handles display of file selection at start of parse flow

    Category: Parse
    :param request: django request object
    :return: response object
    """

    from .ua_parser import get_player_names
    from .forms import fileSelector
    from .models import csvDocument
    from .helpers import not_blank_or_anonymous

    logger = logging.getLogger(__name__)

    # TODO: clean session?

    filelist = []

    # apparently dynamic choices should be done via foreignkey?
    # choices needs a list of 2-tuples, [value, humanreadable]

    if settings.DEBUG:
        logger.warning('presenting parsed objects as parseable')
        for obj in csvDocument.objects.all():
            if obj.parsed:
                filelist.append((obj.id, 'parsed: '+str(obj)))
            else:
                filelist.append((obj.id, str(obj)))
    else:
        for obj in csvDocument.objects.filter(parsed=False):
            filelist.append((obj.id, str(obj)))

    if request.method == 'POST':
        form = fileSelector(request.POST, choices=filelist)
        if form.is_valid():
            fileobj_id = form.cleaned_data['filechoice']
            request.session['file_obj_pk'] = fileobj_id
            player_list = [x for x in get_player_names(fileobj_id) if not_blank_or_anonymous(x)]
            # TODO (lp) why are there blank names
            request.session['player_list'] = player_list

            return redirect('parse_validate_team')
    else:
        form = fileSelector(choices=filelist)
        return render(request, 'db_output/parse_select.html', {'form': form})


def parse_validate_team(request):
    """
    Handles display of team validation page

    :param request:
    :return: response
    """
    from django.forms import modelformset_factory
    from .models import csvDocument, Team
    from .forms import TeamValidationForm

    logger = logging.getLogger(__name__)

    fileobj_id = request.session['file_obj_pk']
    fileobj = csvDocument.objects.get(pk=fileobj_id)
    uploaded_team_name = fileobj.your_team_name
    uploaded_season = fileobj.season

    TeamFormSet = modelformset_factory(Team, form=TeamValidationForm)
    # initial_data = [{'your_team_name': 'New Team Name', 'origin': 'Place Of Origin', 'division': 'M, W, X'}]

    if request.method == 'POST':
        formset = TeamFormSet(request.POST, queryset=Team.objects.filter(team_name__icontains=uploaded_team_name))
        if formset.is_valid():  # will only return valid if all forms are valid
            selected_index = int(request.POST['selector'])  # 1-based form index (1 being first provided match)
            for index, form in enumerate(formset.forms, 1):
                if index == selected_index:
                    saved_team = form.save()
                    request.session['team_obj_pk'] = saved_team.team_ID

            return redirect('parse_validate_player')

    else:  # GET
        formset = TeamFormSet(queryset=Team.objects.filter(team_name__icontains=uploaded_team_name))

    return render(request, 'db_output/parse_validate_team.html', {'formset': formset, 'team_name': uploaded_team_name,
                                                                  'season': uploaded_season})


def parse_validate_player(request):
    """
    Handles display of player validation pages

    Category: Parse
    :param request: django request object
    :return: response object
    """
    from django.forms import modelformset_factory, model_to_dict
    from .models import Player
    from .forms import PlayerNameValidationForm, PlayerDetailValidationForm
    from .helpers import get_best_match

    logger = logging.getLogger(__name__)

    player_list = request.session['player_list']

    NameFormSet = modelformset_factory(Player, form=PlayerNameValidationForm, extra=0)
    DetailFormSet = modelformset_factory(Player, form=PlayerDetailValidationForm, extra=0)

    # generate initial matches
    matched_pks = []
    for csv_name in player_list:
        matched_pks.append(get_best_match(csv_name))

    # create dict for ajax
    match_dict = {}
    for i in range(0, len(matched_pks)):
        matched_player = Player.objects.get(pk=matched_pks[i])
        match_dict[i] = (matched_player.pk, str(matched_player))
    request.session['match_dict'] = match_dict

    if request.method == 'POST':
        name_formset = NameFormSet(request.POST,
                                   queryset=Player.objects.filter(pk__in=matched_pks), prefix='names')
        detail_formset = DetailFormSet(request.POST,
                                       queryset=Player.objects.filter(pk__in=matched_pks), prefix='details')
        if name_formset.is_valid() and detail_formset.is_valid():
            new_to_create = []
            existing_to_update = []

            to_confirm = []

            index = 0
            for nameform, detailform in zip(name_formset, detail_formset):
                # cleaned_data['player_ID'] returns the Player object
                csv_name = player_list[index]

                this_player = detailform.save(commit=False)
                this_player_info = model_to_dict(this_player)

                if not nameform.cleaned_data['match_present_and_selected']:  # if new player required
                    this_player_info['player_ID'] = None  # else will be player_ID from detail form (old)
                    new_to_create.append((csv_name, this_player_info))
                else:
                    existing_to_update.append((csv_name, this_player_info))

                # this is not presented as editable, so we must append it manually
                if csv_name not in this_player_info['csv_names']:
                    new = this_player_info['csv_names'] + ',' + csv_name
                    this_player_info['csv_names'] = new

                to_confirm.append((csv_name, this_player_info))

                index += 1

            # data for display
            request.session['to_confirm'] = to_confirm
            # data for database operations after confirm
            request.session['existing_to_update'] = existing_to_update
            request.session['new_to_create'] = new_to_create

            return HttpResponseRedirect('parse_verify')

        else:
            logger.warning('request.method = ' + str(request.method))
            if name_formset.is_valid():
                warning_string = 'Detail forms were not valid'
                logger.warning(detail_formset.errors)
            elif detail_formset.is_valid():
                warning_string = 'Name forms were not valid'
                logger.warning(name_formset.errors)
            else:
                warning_string = 'All forms were not valid'

            name_formset = NameFormSet(queryset=Player.objects.filter(pk__in=matched_pks), prefix='names')
            detail_formset = DetailFormSet(queryset=Player.objects.filter(pk__in=matched_pks), prefix='details')

            return render(request, 'db_output/parse_validate_player.html', context={'warning': warning_string,
                                                                                    'player_list': player_list,
                                                                                    'name_formset': name_formset,
                                                                                    'detail_formset': detail_formset})

    elif request.method == 'GET':
        name_formset = NameFormSet(queryset=Player.objects.filter(pk__in=matched_pks), prefix='names')
        detail_formset = DetailFormSet(queryset=Player.objects.filter(pk__in=matched_pks), prefix='details')

        return render(request, 'db_output/parse_validate_player.html', context={'player_list': player_list,
                                                                                'name_formset': name_formset,
                                                                                'detail_formset': detail_formset})


def get_initial_match(request):
    """
    called only by ajax - validation_jquery.js

    :param request:
    :return: json
    """
    match_dict = request.session['match_dict']
    full_element_id = request.POST['form_id']
    prefix, form_id, field_id = full_element_id.split('-')

    match_id, match_text = match_dict[form_id]

    return JsonResponse({'success': True,
                         'match_text': match_text,
                         'match_id': match_id})


def update_player_details_form(request):
    """
    called only by ajax - validation_jquery.js

    :param request:
    :return: json
    """
    from .models import Player

    logger = logging.getLogger(__name__)
    # logger.debug(request.session['player_list'])

    full_element_id = request.POST['form_id']
    # select2 boxes are id'd in format : id_names-*-proper_name
    prefix, form_id, field_id = full_element_id.split('-')

    selected_player = Player.objects.get(pk=request.POST['selection_data'])

    field_data = {'player_ID': selected_player.player_ID,
                  'proper_name': selected_player.proper_name,
                  'hometown': selected_player.hometown,
                  'position': selected_player.position,
                  'nickname': selected_player.nickname,
                  'numbers': selected_player.numbers}

    return JsonResponse({'field_data': field_data,
                         'success': True,
                         'form_id': form_id})


def parse_verify(request):
    """
    Handles display of parse output verification page

    Category: Parse
    :param request: django request object
    :return: response object
    """
    from .forms import VerifyConfirmForm
    logger = logging.getLogger(__name__)

    to_confirm = request.session['to_confirm']

    if request.method == 'GET':
        logger.warning('arrived at verify output via GET')
        verify_form = VerifyConfirmForm()

        return render(request, 'db_output/parse_verify.html', context={'verification_needed': to_confirm,
                                                                       'verify_form': verify_form})
    elif request.method == 'POST':
        verify_form = VerifyConfirmForm(request.POST)
        if verify_form.is_valid():
            if 'verify' in verify_form.cleaned_data:
                request.session['verify'] = verify_form.cleaned_data['verify']
                logger.info('verify in cleaned data as: '+str(verify_form.cleaned_data['verify']))
            return HttpResponseRedirect('parse_results')


def parse_results(request):
    """
    Handles display of parse results

    Category: Parse
    :param request: request
    :return: response
    """
    from .ua_parser import parse
    from .models import Player, Team

    # TODO (testing) break out logic into more easily testable funcs

    # if not request.referrer == 'parse_verify':
    #     raise (some error that sends us home)

    all_players = []
    temp_dict = request.session['conversion_dict']

    for csv_name, player_info in request.session['new_to_create']:
        p = Player(**player_info)
        p.save()
        temp_dict[csv_name] = p.player_ID
        all_players.append(p)

    for csv_name, player_info in request.session['existing_to_update']:
        p = Player.objects.get(pk=player_info['player_ID'])

        # TODO (now) this results in blanks being added to blanks with just a comma
        # and also duplicate csv_names
        numbers_now = p.numbers
        p.numbers = numbers_now + ',' + str(player_info.pop('numbers'))
        csv_names_now = p.csv_names
        p.csv_names = csv_names_now + ',' + str(player_info.pop('csv_names'))

        for attr, value in player_info.items():
            setattr(p, attr, value)

        p.save()
        temp_dict[csv_name] = p.player_ID
        all_players.append(p)

    temp_dict['Anonymous'] = -1
    request.session['conversion_dict'] = temp_dict
    # this means that in ua_parser it won't fail when we reach a blank name
    # handle_check_player will see this and do well with it

    team_obj_pk = request.session['team_obj_pk']

    this_team = Team.objects.get(pk=team_obj_pk)
    for player in all_players:
        # establish m2m relationship
        this_team.players.add(player.player_ID)
    this_team.save()

    # TODO (lp): show ALL data that will be saved to db in humanreadable format

    parsed_results = parse(request.session['file_obj_pk'], team_obj_pk,
                           request.session['conversion_dict'], verify=request.session['verify'])
    # currently this just gives us a success indicating string

    return render(request, 'db_output/parse_select.html', context={'parsed_results': parsed_results})


def analysis_select(request):
    """
    Handles display of analysis selector

    Category: Analysis
    :param request: request
    :return: response
    """
    from .forms import AnalysisForm
    from .analysis import get_all_analyses

    # TODO (feat): select all games by tournament

    logger = logging.getLogger(__name__)

    # django forms don't like it when we pass functions as the value in (value, name) tuple of analysis_choices
    # so we can index it, then get back an index which will match a function in the actual list
    analysis_options = get_all_analyses()

    indexed_analysis_options = enumerate(analysis_options)
    widget_choices = []
    for a_index, a_tuple in indexed_analysis_options:
        widget_choices.append((a_index, a_tuple[1]))  # tuple is (obj, name)

    if request.method == 'GET':
        aform = AnalysisForm(analysis_choices=widget_choices)

        return HttpResponse(render(request, 'db_output/analysis_select.html', {'selector': aform}))

    elif request.method == 'POST':
        aform = AnalysisForm(request.POST, analysis_choices=widget_choices)
        if aform.is_valid():
            func_indices = aform.cleaned_data['analysischoice']
            games = aform.cleaned_data['games']
            team = aform.cleaned_data['team']

            display_list = []
            display_table = []
            for a_index in func_indices:

                new_data, display_format = analysis_options[int(a_index)][0](games=games, team=team)
                if display_format == 'table':
                    display_table.append(new_data)
                else:
                    display_list.append(new_data)

            return HttpResponse(render(request, 'db_output/analysis_present.html', {'display_list': display_list,
                                                                                    'display_table': display_table}))

        else:
            logger.warning('form not valid')
            aform = AnalysisForm(analysis_choices=widget_choices)
            return HttpResponse(render(request, 'db_output/analysis_select.html', {'selector': aform}))

