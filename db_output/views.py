# views.py
# contains the logic for presenting all non-trivial pages on the site

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
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

    # TODO: clean session

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

            return redirect('parse_validate_player')
    else:
        form = fileSelector(choices=filelist)
        return render(request, 'db_output/parse_select.html', {'form': form})


def parse_validate_player(request):
    """
    Handles display of player validation pages

    Category: Parse
    :param request: django request object
    :return: response object
    """
    # from .models import Player
    from .forms import ValidationForm, VerifyConfirmForm
    from .helpers import fetch_match
    logger = logging.getLogger(__name__)

    # FIXME: if you refresh you redo the GET part with no processing

    # TODO (soon): replace radio with select2 search by type modelForm

    # this view should have three branches
    # 1 - GET
    # 2 - POST w/ no names remaining
    # 3 - POST w/ names remaining

    player_list = request.session['player_list']

    # Branch 1:
    if request.method == 'GET':
        csv_name = player_list.pop()
        request.session['player_list'] = player_list
        request.session['prev_csv_name'] = csv_name

        # these are to store data so that we can do the database operations in the next view (after confirm is pressed)
        # saving pickled objects to session is EXTREMELY INSECURE if using untrusted session engine (like cookies)
        # this code here won't change if the session engine ever changes
        # unpickling can result in arbitrary code execution
        request.session['matched_to_update'] = []
        request.session['nonmatched_to_create'] = []

        match = fetch_match(csv_name)
        name_validation_form = ValidationForm(match=match)

        request.session['conversion_dict'] = {}
        return render(request, 'db_output/parse_validate_player.html',
                      context={'form': name_validation_form, 'csv_name': csv_name, 'results': str(player_list)})

    # Branch 2 and 3:
    if request.method == 'POST':

        nonmatched_to_create = request.session['nonmatched_to_create']
        matched_to_update = request.session['matched_to_update']
        csv_name = request.session['prev_csv_name']
        match = fetch_match(csv_name)

        # Branch 3
        name_validation_form = ValidationForm(request.POST, match=match)
        # not supplying match here makes the form set a custom name to required, and then the next line returns False
        if name_validation_form.is_valid():
            results = name_validation_form.cleaned_data

            # conversion dict will be { csv_name : actual_player_pk }
            new_dict = request.session['conversion_dict']

            # this means that if there is no match, regardless of form choice, the custom name provided will be used
            # if there is no match, the form will require a custom name to be inputted
            if results['selection'] == 'provided' and match:
                # find player object based on match, put in pk
                new_dict[csv_name] = match.player_ID
                match.csv_names = match.csv_names + ',' + csv_name
                matched_to_update.append(match.player_ID)

            else:
                given_name = results['custom_name']
                # when we create conversion dict from custom names we do not know their pks yet bc no object
                # that is why conversion dict is empty on this page after a fully new team
                # this will be written over with new pks in parse_results (after confirmation)

                # new_dict[csv_name] = 'newly added player, ID to be created on confirmation'
                new_dict[csv_name] = given_name
                nonmatched_to_create.append((given_name, csv_name))

            request.session['conversion_dict'] = new_dict
            request.session['nonmatched_to_create'] = nonmatched_to_create
            request.session['matched_to_update'] = matched_to_update

            # Branch 2:
            if not player_list:  # if we have looped over everyone
                to_confirm = []
                temp_dict = request.session['conversion_dict']
                for k, v in temp_dict.items():
                    to_confirm.append((k, v))

                logger.debug('sending to parse_verify')
                request.session['to_confirm'] = to_confirm
                return redirect('parse_verify')

            csv_name = player_list.pop()
            request.session['player_list'] = player_list
            request.session['prev_csv_name'] = csv_name
            match = fetch_match(csv_name)
            name_validation_form = ValidationForm(match=match)

            return render(request, 'db_output/parse_validate_player.html',
                          context={'form': name_validation_form,
                                   'csv_name': csv_name,
                                   'results': str(request.session['conversion_dict'])})

        else:
            # reload the page with everything as it was if invalid input
            name_validation_form = ValidationForm(match=match)
            return render(request, 'db_output/parse_validate_player.html',
                          context={'form': name_validation_form,
                                   'csv_name': csv_name,
                                   'results': 'Data entered was not valid, please retry'})


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
    # TODO (lp): show ALL data that will be saved to db in humanreadable format
    # TODO: take in additional information about players

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
    from . import models

    # TODO (testing) break out logic into more easily testable funcs

    # TODO: control flow into parse_results because we do db work here
    # if not request.referrer == 'parse_verify':
    #     raise (some error that sends us home)

    all_players = []
    for player_pk in request.session['matched_to_update']:
        p = models.Player.objects.get(pk=player_pk)
        p.save()
        all_players.append(p)

    for given_name, csv_name in request.session['nonmatched_to_create']:
        p = models.Player(proper_name=given_name, csv_names=csv_name)
        p.save()
        all_players.append(p)
        temp_dict = request.session['conversion_dict']
        temp_dict[csv_name] = p.player_ID
        request.session['conversion_dict'] = temp_dict

    temp_dict = request.session['conversion_dict']
    temp_dict['Anonymous'] = -1
    request.session['conversion_dict'] = temp_dict
    # this means that in ua_parser it won't fail when we reach a blank name
    # handle_check_player will see this do well with it

    # creating the player objects can happen here, and therefore creating the team object is ok
    # both should be persistent beyond the scope of a single csv, and thus parse call

    # TODO: manually validate team names like player names

    fileobj = models.csvDocument.objects.get(pk=request.session['file_obj_pk'])
    team_name = fileobj.your_team_name

    # confirm which players were present in colony v thunder, check against analysis results

    if models.Team.objects.filter(team_name=team_name).exists():
        team_obj_pk = models.Team.objects.get(team_name=team_name).team_ID  # TODO: handle multiple team matches
    else:
        new_team = models.Team(team_name=team_name)
        new_team.save()
        team_obj_pk = new_team.team_ID

    this_team = models.Team.objects.get(pk=team_obj_pk)
    for player in all_players:
        # establish m2m relationship
        this_team.players.add(player.player_ID)
    this_team.save()

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
    from .analysis import get_all_analyses, null_analysis, second_null_analysis

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

