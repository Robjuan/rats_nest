from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import logging


def index(request):
    logger = logging.getLogger(__name__)
    logger.info('index.html accessed')
    return HttpResponse(render(request, 'db_output/index.html', {}))


def contact_us(request):
    return HttpResponse(render(request, 'db_output/contact_us.html', {}))


def not_blank_or_anonymous(name):
    # 'Anonymous' is inserted by UA for "other team" stats, and Throwaways (as receiver)
    if name and name != 'Anonymous':
        return True
    else:
        if not name:
            logger = logging.getLogger(__name__)
            logger.debug('Blank name being filtered')
        return False


def test_output(request):

    from .ua_parser import get_player_names
    from .forms import fileSelector
    from .models import csvDocument

    logger = logging.getLogger(__name__)

    filelist = []

    # TODO (lp): streamline data input?

    # apparently dynamic choices should be done via foreignkey?
    # choices needs a list of 2-tuples, [value, humanreadable]

    if settings.DEBUG:
        for obj in csvDocument.objects.all():
            logger.warning('presenting parsed objects as parseable')
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

            return HttpResponseRedirect('confirm_upload_details')
    else:
        form = fileSelector(choices=filelist)
        return render(request, 'db_output/show_output.html', {'form': form})


def insert_test_data(request):

    # PLEASE BE VERY CAREFUL WITH MANUAL ADDITION AND SUBTRACTION
    # Use the Admin portal for one offs

    please_confirm_insert = False
    please_confirm_delete = False

    if please_confirm_insert and settings.DEBUG:
        from .models import Player, Team
        p = Player(proper_name='Anonymous', hometown='San Francisco, CA', csv_names='Anonymous')
        p.save()

        t = Team(team_name='Default_team', origin='San Francisco, CA', division='Mixed')
        t.save()
        text = 'You have inserted:' + str(p) + ' and ' + str(t)

    elif please_confirm_delete and settings.DEBUG:
        from .models import csvDocument
        for i in range(1, 5):
            csvDocument.objects.filter(id=i).delete()
        text = 'deleted'

    else:
        text = 'Nothing to see here'

    return HttpResponse(text)


def upload_csv(request):
    from .forms import csvDocumentForm

    # TODO (feat): take in more information about the game (location, conditions etc)
    # use tags for conditions

    # this permission check might be duplicative as it is also checked in the template
    # TODO: this permission doesn't actually exist, but rob_development is a superuser so has_perm always returns True
    # so is rats_development

    if request.method == 'POST' and request.user.has_perm('db_output.can_upload_csv'):
        form = csvDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # TODO: check we're not saving/parsing the same game (datetime, tournament name)
            return HttpResponseRedirect('test_output')  # show if something got added
    else:
        form = csvDocumentForm()
        return render(request, 'db_output/upload_csv.html', {'form': form})


def fetch_match(csv_name):
    from .models import Player

    for stored_player in Player.objects.all():
        if csv_name in stored_player.csv_names or csv_name == stored_player.proper_name:
            return stored_player

    # only if no match found
    return None


def confirm_upload_details(request):
    # from .models import Player
    from .forms import ValidationForm, VerifyConfirmForm
    logger = logging.getLogger(__name__)

    # FIXME: if you refresh you redo the GET part with no processing

    # TODO: replace radio with select2 search by type modelForm

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
        return render(request, 'db_output/confirm_upload_details.html',
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
                # this will be written over with new pks in display_parse_results (after confirmation)

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

                # TODO (lp): show ALL data that will be saved to db in humanreadable format


                # TODO: include "verify" checkbox - we'll need a view to process the post of verify?
                request.session['verify'] = True
                verify_confirm = VerifyConfirmForm()

                logger.debug('sending to verify_output')
                return render(request, 'db_output/verify_output.html', context={'to_confirm': to_confirm,
                                                                                'verify_confirm': verify_confirm,
                                                                                'extra_head': __name__})

            csv_name = player_list.pop()
            request.session['player_list'] = player_list
            request.session['prev_csv_name'] = csv_name
            match = fetch_match(csv_name)
            name_validation_form = ValidationForm(match=match)

            return render(request, 'db_output/confirm_upload_details.html',
                          context={'form': name_validation_form,
                                   'csv_name': csv_name,
                                   'results': str(request.session['conversion_dict'])})

        else:
            # reload the page with everything as it was if invalid input
            name_validation_form = ValidationForm(match=match)
            return render(request, 'db_output/confirm_upload_details.html',
                          context={'form': name_validation_form,
                                   'csv_name': csv_name,
                                   'results': 'Data entered was not valid, please retry'})


def verify_output(request):
    from .forms import VerifyConfirmForm
    logger = logging.getLogger(__name__)

    if request.method == 'GET':
        logger.warning('arrived at verify output via GET')

    elif request.method == 'POST':
        verify_confirm = VerifyConfirmForm(request.POST)
        if verify_confirm.is_valid():
            if 'verify' in verify_confirm.cleaned_data:
                request.session['verify'] = verify_confirm.cleaned_data['verify']

            request.session['go_to_dpr'] = True
            return HttpResponseRedirect('display_parse_results')


def display_parse_results(request):

    from .ua_parser import parse
    from . import models

    if 'go_to_dpr' not in request.session:
        return HttpResponseRedirect('index')  # TODO (lp) is this insecure?

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

    # creating the player objects can happen here, and therefore creating the team object is ok
    # both should be persistent beyond the scope of a single csv, and thus parse call

    # TODO: manually validate team names like player names

    fileobj = models.csvDocument.objects.get(pk=request.session['file_obj_pk'])
    team_name = fileobj.your_team_name

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

    return render(request, 'db_output/show_output.html', context={'parsed_results': parsed_results})


def present_stats(request):
    from .forms import AnalysisForm
    from .analysis import get_all_analyses, null_analysis, second_null_analysis

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

        return HttpResponse(render(request, 'db_output/present_stats.html', {'selector': aform}))

    elif request.method == 'POST':
        aform = AnalysisForm(request.POST, analysis_choices=widget_choices)
        if aform.is_valid():
            func_indices = aform.cleaned_data['analysischoice']
            game = aform.cleaned_data['game']
            team = aform.cleaned_data['team']

            results = []
            for a_index in func_indices:

                new_data = analysis_options[int(a_index)][0](game=game, team=team)

                results.append(new_data)
            return HttpResponse(render(request, 'db_output/present_stats.html', {'analysis': str(results)}))

        else:
            logger.warning('form not valid')
            aform = AnalysisForm(analysis_choices=widget_choices)
            return HttpResponse(render(request, 'db_output/present_stats.html', {'selector': aform}))

