from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

# only required for method 2 , simple saving
from django.core.files.storage import default_storage


def index(request):
    return HttpResponse(render(request, 'db_output/index.html', {}))


def contact_us(request):
    return HttpResponse(render(request, 'db_output/contact_us.html', {}))


def not_blank_or_anonymous(name):
    # 'Anonymous' is inserted by UA for "other team" stats, and Throwaways (as receiver)
    if name and name != 'Anonymous':
        return True
    else:
        return False


def test_output(request):

    from .ua_parser import get_player_names
    from .forms import fileSelector
    from .models import csvDocument

    filelist = []

    # TODO (lp): streamline data input?

    # apparently dynamic choices should be done via foreignkey?
    # choices needs a list of 2-tuples, [value, humanreadable]

    for obj in csvDocument.objects.all():      # TODO (db): redo with better query
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

    if please_confirm_insert:
        from .models import Player, Team
        p = Player(proper_name='Anonymous', hometown='San Francisco, CA', csv_names='Anonymous')
        p.save()

        t = Team(team_name='Default_team', origin='San Francisco, CA', division='Mixed')
        t.save()
        text = 'You have inserted:' + str(p) + ' and ' + str(t)

    elif please_confirm_delete:
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

    # TODO (db): redo this with a more efficient query

    for stored_player in Player.objects.all():
        if csv_name in stored_player.csv_names or csv_name == stored_player.proper_name:
            return stored_player  # TODO (lp): handle multiple matches

    # only if no match found
    return None


def confirm_upload_details(request):
    # from .models import Player
    from .forms import ValidationForm

    # FIXME: if you refresh you redo the GET part with no processing

    # TODO: take in more information about the player, compare on more than name

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
                results = []
                temp_dict = request.session['conversion_dict']
                for k, v in temp_dict.items():
                    results.append((k, v))

                # TODO (lp): best format for showing this to the user before confirmation?

                return render(request, 'db_output/show_output.html', context={'results': results})

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
            # reload the page with everything as it was
            name_validation_form = ValidationForm(match=match)
            return render(request, 'db_output/confirm_upload_details.html',
                          context={'form': name_validation_form,
                                   'csv_name': csv_name,
                                   'results': 'Data entered was not valid, please retry'})


def display_parse_results(request):

    from .ua_parser import parse
    from . import models

    # we get to this view from confirm being pushed # TODO: make sure that's the only way
    # if not (where we came from) == (confirm_upload_details)
    #   return home

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

    parsed_results = parse(request.session['file_obj_pk'], team_obj_pk, request.session['conversion_dict'])
    # currently this just gives us a success indicating string

    return render(request, 'db_output/show_output.html', context={'parsed_results': parsed_results})




