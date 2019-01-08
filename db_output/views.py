from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

# only required for method 2 , simple saving
from django.core.files.storage import default_storage


def index(request):

    return HttpResponse(render(request, 'db_output/index.html', {}))


def test_output(request):

    from .ua_parser import get_player_names
    from .forms import fileSelector
    from .models import csvDocument

    filelist = []

    # apparently dyanmic choices should be done via foreignkey?
    # choices needs a list of 2-tuples, "[value, humanreadable]

    for obj in csvDocument.objects.all():      # hope this isn't too resource-intensive
        filelist.append((obj, str(obj)))

    if request.method == 'POST':
        form = fileSelector(request.POST, choices=filelist)
        if form.is_valid():

            fileobj = form.cleaned_data['filechoice']
            request.session['file_obj_pk'] = fileobj.id
            request.session['player_list'] = get_player_names(fileobj.file)

            return HttpResponseRedirect('confirm_upload_details')
    else:
        form = fileSelector(choices=filelist)
        return render(request, 'db_output/show_output.html', {'form': form})


def insert_test_data(request):

    from .models import Player
    p = Player(proper_name='homer simpson', hometown='evergreen terrace')
    p.save()

    # print(Players.objects.all())

    return HttpResponse('You have inserted '+str(p))


def upload_csv(request):
    from .forms import csvDocumentForm

    # this permission check might be duplicative as it is also checked in the template
    # TODO: this permission doesn't actually exist, but rob_development is a superuser so has_perm always returns True

    if request.method == 'POST' and request.user.has_perm('db_output.can_upload_csv'):
        form = csvDocumentForm(request.POST, request.FILES)
        if form.is_valid():

            # METHOD 1 : save to "default storage" as a simple file
            # file = request.FILES['file']
            # file_name = default_storage.save(file.name, file)

            # METHOD 2 : save to the database as part of a model
            form.save()
            # we need to save who took the stats to be able to restrict access
            # saving as a model allows this sort of shit
            # we can work on offsite storage of the csv later

            return HttpResponseRedirect('test_output')  # show if something got added
    else:
        form = csvDocumentForm()
        return render(request, 'db_output/upload_csv.html', {'form': form})


def confirm_upload_details(request):
    from .models import Player
    from .forms import ValidationForm

    player_list = request.session['player_list']
    if not player_list: # if we have looped over everyone
        results = []
        temp_dict = request.session['conversion_dict']
        for key in temp_dict.keys():
            results.append((key, temp_dict[key]))

        return render(request, 'db_output/show_output.html', context={'results': results})

    # TODO: we might be dropping the first player because pop on GET??
    csv_name = player_list.pop()  # calling pop directly on session doesn't work - this does
    if csv_name == 'Anonymous':  # inserted by UA for "other team" stats
        csv_name = player_list.pop()
    request.session['player_list'] = player_list

    match = None
    for stored_player in Player.objects.all():
        if csv_name in stored_player.csv_names:
            match = str(stored_player)

    # these are to store data so that we can do the database operations in the next view (after confirm is pressed)
    # saving pickled objects to session is EXTREMELY INSECURE if using untrusted session engine (like cookies)
    # this code here won't change if the session engine ever changes
    # unpickling can result in arbitrary code execution

    if 'matched_to_update' in request.session:
        matched_to_update = request.session['matched_to_update']
    else:
        matched_to_update = []

    if 'nonmatched_to_create' in request.session:
        nonmatched_to_create = request.session['nonmatched_to_create']
    else:
        nonmatched_to_create = []

    name_validation_form = ValidationForm(match=match)

    if request.method == 'POST':
        name_validation_form = ValidationForm(request.POST, match=match)  # TODO: make the form empty on second visit
        if name_validation_form.is_valid():
            results = name_validation_form.cleaned_data

            # conversion dict will be { csv_name : actual_player_pk }
            new_dict = request.session['conversion_dict']

            if results['selection'] == 'provided':
                # find player object based on match, put in pk
                new_dict[csv_name] = stored_player.player_ID
                stored_player.csv_names = stored_player.csv_names + ',' + csv_name
                matched_to_update.append(stored_player.player_ID)

            elif results['selection'] == 'custom':
                given_name = results['custom_name']

                nonmatched_to_create.append((given_name, csv_name))

            request.session['conversion_dict'] = new_dict
            request.session['nonmatched_to_create'] = nonmatched_to_create
            request.session['matched_to_update'] = matched_to_update

            return render(request, 'db_output/confirm_upload_details.html',
                          context={'form': name_validation_form, 'csv_name': csv_name, 'results': results})
    else:
        request.session['conversion_dict'] = {}
        return render(request, 'db_output/confirm_upload_details.html',
                      context={'form': name_validation_form, 'csv_name': csv_name})


def display_parse_results(request):

    from .ua_parser import parse
    from . import models

    # we get to this view from confirm being pushed # TODO: make sure that's the only way

    for player_pk in request.session['matched_to_update']:
        p = models.Player.objects.get(pk=player_pk)
        p.save()

    for given_name, csv_names in request.session['nonmatched_to_create']:
        p = models.Player(proper_name=given_name, csv_names=csv_names)
        p.save()

    # creating the player objects can happen here, and therefore creating the team object is ok
    # both should be persistent beyond the scope of a single csv, and thus parse call
    # TODO: validate team names? fuck idk tho

    fileobj = models.csvDocument.objects.get(pk=request.session['file_obj_pk'])
    team_name = fileobj.your_team_name
    for existing_team in models.Team.objects.all():
        if existing_team.team_name == team_name:
            team_obj_pk = existing_team.team_ID
        else:
            new_team = models.Team(team_name=team_name)
            new_team.save()
            team_obj_pk = new_team.team_ID


    # TODO: ADD PLAYERS TO TEAM !!!

    content = parse(request.session['file_obj_pk'], team_obj_pk, request.session['conversion_dict'])
    # currently this just gives us a success indicating string

    return render(request, 'db_output/base.html', context={'content': content})
