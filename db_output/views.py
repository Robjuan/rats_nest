# views.py
# contains the logic for presenting all non-trivial pages on the site

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.db import transaction

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

    filelist = []

    # choices needs a list of 2-tuples, [value, humanreadable]

    # TODO (lp) make this a login required checkbox on the page

    if settings.DEBUG:
        for obj in csvDocument.objects.all().order_by('your_team_name'):
            if obj.parsed:
                filelist.append((obj.id, 'parsed: '+str(obj)))
            else:
                filelist.append((obj.id, str(obj)))
    else:
        for obj in csvDocument.objects.filter(parsed=False).order_by('your_team_name'):
            filelist.append((obj.id, str(obj)))

    if request.method == 'POST':
        form = fileSelector(request.POST, choices=filelist)
        if form.is_valid():
            fileobj_id = form.cleaned_data['filechoice']
            request.session['file_obj_pk'] = fileobj_id
            player_list = [x for x in get_player_names(fileobj_id) if not_blank_or_anonymous(x)]
            request.session['player_list'] = player_list

            return redirect('parse_validate_team')
    else:
        if settings.DEBUG:
            logger.warning('presenting parsed objects as parseable')

        form = fileSelector(choices=filelist)
        return render(request, 'db_output/parse_select.html', {'form': form})


def parse_validate_team(request):
    """
    Handles display of team validation page

    :param request:
    :return: response
    """
    from .models import csvDocument, Team
    from .forms import get_primary_validation_form, get_secondary_validation_form
    from .helpers import get_best_match, generate_active_form_dict
    from collections import OrderedDict

    logger = logging.getLogger(__name__)

    fileobj_id = request.session['file_obj_pk']
    fileobj = csvDocument.objects.get(pk=fileobj_id)
    uploaded_team_name = fileobj.your_team_name
    uploaded_season = fileobj.season
    request.session['season'] = uploaded_season
    request.session['filename_for_display'] = fileobj.file.name

    primary_form_factory = get_primary_validation_form(Team, 'team_name')
    secondary_form_factory = get_secondary_validation_form(Team)

    if request.method == 'GET':

        # create dict for ajax (one form, one item)
        match_dict = OrderedDict()
        match_pk = get_best_match(Team, uploaded_team_name)
        if match_pk:
            matched_team = Team.objects.get(pk=match_pk)
            match_dict['team_name'] = (matched_team.pk, str(matched_team))
        else:
            match_dict['team_name'] = (None, 'No match found')

        request.session['match_dict'] = match_dict

        # if there is no match, jquery will set the secondary form to be the active choice to start
        # otherwise, the primary form will be the one to start

        request.session['active_form_dict'] = generate_active_form_dict(match_dict)

        primary_form = primary_form_factory()
        secondary_form = secondary_form_factory()

        return render(request, 'db_output/parse_validate_team.html', {'primary_form': primary_form,
                                                                      'secondary_form': secondary_form,
                                                                      'team_name': uploaded_team_name,
                                                                      'season': uploaded_season,
                                                                      'filename': request.session[
                                                                          'filename_for_display']})

    if request.method == 'POST':
        primary_form = primary_form_factory(request.POST)
        secondary_form = secondary_form_factory(request.POST)

        # whilst the GET view is active (before we are here in post)
        # active_form_dict will be updated by ajax to have 1 or 2 depending on which form is active

        active_form_dict = request.session['active_form_dict']
        for key, value in active_form_dict.items():
            if value == 1 and primary_form.is_valid():
                form_data = primary_form.cleaned_data
                saved_team = Team.objects.get(pk=int(form_data['team_name']))
                # select2 form returns pk as form data
                # logger.debug(saved_team)

            elif value == 2 and secondary_form.is_valid():
                saved_team = secondary_form.save()
                # logger.debug(saved_team)
            else:
                logger.error('active_form_dict malformed or forms not valid')
                return render(request, 'db_output/parse_validate_team.html', {'primary_form': primary_form,
                                                                              'secondary_form': secondary_form,
                                                                              'team_name': uploaded_team_name,
                                                                              'season': uploaded_season,
                                                                              'filename': request.session[
                                                                                  'filename_for_display']})

            request.session['team_obj_pk'] = saved_team.team_ID
            request.session['active_form_dict'] = None
            return redirect('parse_validate_opposition')


def parse_validate_opposition(request):
    """
    handles display of opposition verification

    :param request:
    :return:
    """
    from .forms import get_secondary_validation_form, get_primary_validation_form
    from .models import Team

    logger = logging.getLogger(__name__)

    primary_form_factory = get_primary_validation_form(Team, 'team_name')
    secondary_form_factory = get_secondary_validation_form(Team)

    uploaded_season = request.session['season']
    request.session['match_dict'] = None

    if request.method == 'GET':
        primary_form = primary_form_factory()
        secondary_form = secondary_form_factory()

        return render(request, 'db_output/parse_validate_opposition.html', {'primary_form': primary_form,
                                                                            'secondary_form': secondary_form,
                                                                            'season': uploaded_season,
                                                                            'filename': request.session[
                                                                                'filename_for_display']})

    if request.method == 'POST':
        primary_form = primary_form_factory(request.POST)
        secondary_form = secondary_form_factory(request.POST)

        active_form_dict = request.session['active_form_dict']
        for key, value in active_form_dict.items():
            if value == 1 and primary_form.is_valid():
                form_data = primary_form.cleaned_data
                saved_team = Team.objects.get(pk=int(form_data['team_name']))
                # select2 form returns pk as form data
                # logger.debug(saved_team)

            elif value == 2 and secondary_form.is_valid():
                # todo (lp) some type of check to warn if you're creating a duplicate team
                saved_team = secondary_form.save()
                # logger.debug(saved_team)
            else:
                logger.error('active_form_dict malformed or forms not valid')
                return render(request, 'db_output/parse_validate_opposition.html', {'primary_form': primary_form,
                                                                                    'secondary_form': secondary_form,
                                                                                    'season': uploaded_season,
                                                                                    'filename': request.session[
                                                                                        'filename_for_display']})

            request.session['opposition_obj_pk'] = saved_team.team_ID
            request.session['active_form_dict'] = None
            return redirect('parse_validate_player')


def parse_validate_player(request):
    """
    Handles display of player validation pages

    Category: Parse
    :param request: django request object
    :return: response object
    """
    from django.forms import modelformset_factory
    from django.db.models import Case, When
    from django.core import serializers
    from .models import Player
    from .forms import get_primary_validation_form, get_secondary_validation_form
    from .helpers import get_best_match, generate_active_form_dict, generate_readable
    from collections import OrderedDict

    logger = logging.getLogger(__name__)

    player_list = request.session['player_list']

    # generate initial matches
    matched_pks = []
    for csv_name in player_list:
        matched_pks.append(get_best_match(Player, csv_name))

    # create dict for ajax
    match_dict = OrderedDict()
    for i in range(0, len(matched_pks)):
        if matched_pks[i]:
            matched_player = Player.objects.get(pk=matched_pks[i])
            match_dict[i] = (matched_player.pk, str(matched_player))

        else:
            match_dict[i] = (None, 'No match found')

    request.session['match_dict'] = match_dict

    preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(matched_pks)])
    formset_queryset = Player.objects.filter(pk__in=matched_pks).order_by(preserved_order)
    empty_queryset = Player.objects.none()
    # only the primary formset will require an actual queryset
    # the secondary forms will always be blank to start
    # hence empty queryset and extra=len(player_list)
    req_extra = len(player_list) - len(formset_queryset)

    primary_formset_factory = modelformset_factory(Player, form=get_primary_validation_form(Player, 'proper_name'),
                                                   extra=req_extra)
    secondary_formset_factory = modelformset_factory(Player, form=get_secondary_validation_form(Player),
                                                     extra=len(player_list))

    if request.method == 'GET':
        request.session['active_form_dict'] = generate_active_form_dict(match_dict)

        primary_formset = primary_formset_factory(queryset=formset_queryset, prefix='names')
        secondary_formset = secondary_formset_factory(queryset=empty_queryset, prefix='details')

        return render(request, 'db_output/parse_validate_player.html', context={'player_list': player_list,
                                                                                'primary_formset': primary_formset,
                                                                                'secondary_formset': secondary_formset,
                                                                                'filename': request.session[
                                                                                    'filename_for_display']})

    if request.method == 'POST':
        active_form_dict = request.session['active_form_dict']

        primary_formset = primary_formset_factory(request.POST, queryset=formset_queryset, prefix='names')
        secondary_formset = secondary_formset_factory(request.POST, queryset=empty_queryset, prefix='details')

        new_to_create = []
        existing_to_update = []
        to_confirm = []

        # primary_formset will not be valid if there are empty (no match, nothing selected) forms
        for index, (primary_form, secondary_form) in enumerate(zip(primary_formset, secondary_formset)):

            # find the item at same index as this form as tuple (form_index, prisec)
            this_active_form = list(active_form_dict.items())[index][1]
            csv_name = player_list[index]

            if this_active_form == 1 and primary_form.is_valid():
                this_player = Player.objects.get(pk=int(primary_form.cleaned_data['proper_name']))
                this_player.add_if_not_blank_or_existing('csv_names', csv_name)
                # this_player_info = serializers.serialize('json', [this_player])
                existing_to_update.append((csv_name, this_player.player_ID))

            elif this_active_form == 2 and secondary_form.is_valid():
                this_player = secondary_form.save(commit=False)
                this_player.add_if_not_blank_or_existing('csv_names', csv_name)
                # serialiser expects a list
                this_player_info = serializers.serialize('json', [this_player])
                new_to_create.append((csv_name, this_player_info))

            else:
                logger.error('error in form validation (this_active_form = ' + str(this_active_form) + ')')
                details = []
                if secondary_form.is_valid():
                    warning_string = 'primary form ' + str(index) + ' invalid'
                    details.append(primary_form.errors)
                elif primary_form.is_valid():
                    warning_string = 'secondary form ' + str(index) + ' invalid'
                    details.append(secondary_form.errors)
                else:
                    details.append(primary_form.errors)
                    details.append(secondary_form.errors)
                    warning_string = 'neither form valid @ index: ' + str(index)

                logger.warning(details)

                primary_formset = primary_formset_factory(queryset=formset_queryset, prefix='names')
                secondary_formset = secondary_formset_factory(queryset=empty_queryset, prefix='details')

                return render(request, 'db_output/parse_validate_player.html', context={'warning': warning_string,
                                                                                        'player_list': player_list,
                                                                                        'primary_formset': primary_formset,
                                                                                        'secondary_formset': secondary_formset,
                                                                                        'filename': request.session[
                                                                                            'filename_for_display']})

            to_confirm.append((csv_name, generate_readable(this_player)))

        # data for display
        request.session['to_confirm'] = to_confirm
        # data for database operations after confirm
        request.session['existing_to_update'] = existing_to_update
        request.session['new_to_create'] = new_to_create

        request.session['match_dict'] = None

        return HttpResponseRedirect('parse_verify')


def parse_verify(request):
    """
    Handles display of parse output verification page

    Category: Parse
    :param request: django request object
    :return: response object
    """
    from .forms import VerifyConfirmForm
    from .models import Team
    logger = logging.getLogger(__name__)

    # TODO (feat): take in more information about the game (location, conditions etc)
    # use tags for conditions

    to_confirm = request.session['to_confirm']

    if request.method == 'GET':
        verify_form = VerifyConfirmForm()

        season = request.session['season']
        team_name = Team.objects.get(pk=request.session['team_obj_pk'])
        try:
            opp_name = Team.objects.get(pk=request.session['opposition_obj_pk'])
        except KeyError:
            opp_name = None

        return render(request, 'db_output/parse_verify.html', context={'verification_needed': to_confirm,
                                                                       'verify_form': verify_form,
                                                                       'team_name': team_name,
                                                                       'season': season,
                                                                       'opp_name': opp_name,
                                                                       'filename': request.session[
                                                                           'filename_for_display']})
    elif request.method == 'POST':
        verify_form = VerifyConfirmForm(request.POST)
        if verify_form.is_valid():
            if 'verify' in verify_form.cleaned_data:
                request.session['verify'] = verify_form.cleaned_data['verify']
                logger.info('verify in cleaned data as: '+str(verify_form.cleaned_data['verify']))
            return HttpResponseRedirect('parse_results')


# atomic means that all db hits from this view will be held up and only executed on successful return
@transaction.atomic()
def parse_results(request):
    """
    Handles display of parse results

    Category: Parse
    :param request: request
    :return: response
    """
    from django.core import serializers
    from .ua_parser import parse
    from .models import Player, Team, csvDocument
    import os

    logger = logging.getLogger(__name__)

    # TODO (testing) break out logic into more easily testable funcs

    # if not request.referrer == 'parse_verify':
    #     raise (some error that sends us home)

    all_players = []
    temp_dict = request.session['conversion_dict']

    for csv_name, player_info in request.session['new_to_create']:
        # deserialise returns a generator, because it expects (and gets) a list
        # next() returns the first (and only) item
        p = next(serializers.deserialize('json', player_info)).object
        p.save()
        temp_dict[csv_name] = p.player_ID
        all_players.append(p)

    for csv_name, player_id in request.session['existing_to_update']:
        p = Player.objects.get(pk=player_id)

        # TODO (lp) - this is being fetched+modified both here and before being saved to the session lists
        # should probably just do it once and serialise from there

        p.add_if_not_blank_or_existing('csv_names', csv_name)

        p.save()
        temp_dict[csv_name] = p.player_ID
        all_players.append(p)

    temp_dict['Anonymous'] = -1
    request.session['conversion_dict'] = temp_dict
    # this means that in ua_parser it won't fail when we reach a blank name
    # handle_check_player will see this and do well with it

    team_obj_pk = request.session['team_obj_pk']

    try:
        opp_pk = request.session['opposition_obj_pk']
    except KeyError:
        opp_pk = False

    this_team = Team.objects.get(pk=team_obj_pk)
    for player in all_players:
        # establish m2m relationship
        this_team.players.add(player.player_ID)
    this_team.save()

    # TODO (lp): show ALL data that will be saved to db in humanreadable format

    parsed_results = parse(request.session['file_obj_pk'], team_obj_pk,
                           request.session['conversion_dict'], verify=request.session['verify'],
                           opposition_pk=opp_pk)
    if not parsed_results:
        logger.critical('parse() returned None')
        raise Exception

    # currently this just gives us a success indicating string

    # move parsed files into media/csv/.archive
    file_obj = csvDocument.objects.get(pk=request.session['file_obj_pk'])
    head, tail = os.path.split(file_obj.file.name)
    new_path = os.path.join(settings.MEDIA_ROOT, 'csv', '.archive', tail)
    try:
        os.rename(file_obj.file.path, new_path)
    except OSError:
        logger.info('.archive directory does not exist, creating')
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'csv', '.archive'))
        os.rename(file_obj.file.path, new_path)
    file_obj.save()

    return render(request, 'db_output/parse_results.html', context={'parsed_results': parsed_results})


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

            content = {}

            display_list = []
            display_table = []
            display_raw = ''

            template = 'db_output/analysis_present.html'

            for a_index in func_indices:

                new_data, display_format = analysis_options[int(a_index)][0](games=games, team=team)

                if display_format == 'table':
                    display_table.append(new_data)

                elif display_format == 'list':
                    display_list.append(new_data)

                else:  # display_format == 'raw'
                    display_raw += str(new_data)

                    # allow redirect to team_stats template by specific display_format string

            return HttpResponse(render(request, template, {'display_list': display_list,
                                                           'display_table': display_table,
                                                           'display_raw': display_raw}))

        else:
            logger.warning('form not valid')
            aform = AnalysisForm(analysis_choices=widget_choices)
            return HttpResponse(render(request, 'db_output/analysis_select.html', {'selector': aform}))


def team_stats(request):
    """
    Produces the team stats overview page
    Gets a team & games selection
    Calls analysis
    Returns something template -> list.js can use

    :param request:
    :return: team_stats
    """
    from .analysis import constructors_test
    from .forms import DataSelectionForm

    logger = logging.getLogger(__name__)

    data_selection_form = DataSelectionForm()

    if request.method == 'GET':
        return HttpResponse(render(request, 'db_output/team_stats.html', {'data_selection_form': data_selection_form}))

    else:  # request.method == 'POST':
        data_selection_form = DataSelectionForm(request.POST)
        if data_selection_form.is_valid():
            games = data_selection_form.cleaned_data['games']
            team = data_selection_form.cleaned_data['team']

            # get rid of this return value stuff quickly
            disp_table, disp_format = constructors_test(team=team, games=games)





        else:
            return HttpResponse(render(request, 'db_output/team_stats.html',
                                       {'data_selection_form': data_selection_form}))

        return render(request, 'db_output/team_stats.html', context={'table': disp_table})
