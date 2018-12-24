from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

# only required for method 2 , simple saving
from django.core.files.storage import default_storage


def index(request):

    return HttpResponse(render(request, 'db_output/index.html', {}))


def test_output(request):

    from .ua_parser import parse
    from .forms import fileSelector
    from .models import csvDocument

    filelist = []

    # apparently dyanmic choices should be done via foreignkey?
    # choices needs a list of 2-tuples, "[value, humanreadable]

    for obj in csvDocument.objects.all():      # hope this isn't too resource-intensive
        filelist.append((obj.file, str(obj)))

    if request.method == 'POST':
        form = fileSelector(request.POST, choices=filelist)
        if form.is_valid():

            # print('cleaned_data: ' + str(form.cleaned_data))

            filename = form.cleaned_data['filechoice']
            # the form always resets to the first option, how to get it to remember?

            # display_txt = parse(filename)
            #return render(request, 'db_output/show_output.html', {'form': form, 'results': display_txt})

            request.session['filename'] = filename
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
    from .forms import playerNameValidationForm
    from .ua_parser import get_player_names

    request.session['player_list'] = get_player_names(request.session['filename'])

    # pull filename from session
    # pull all players mentioned
    # for each player, come back here
    if request.method == 'GET':

        csv_name = request.session['player_list'].pop()

        name_choices = []
        for stored_player in Player.objects.all():
            if csv_name in stored_player.csv_names:
                name_choices.append([stored_player, str(stored_player)])

        if not name_choices:
            name_choices.append(('no player', 'no player'))

        game_details_form = playerNameValidationForm(choices=name_choices,
                                                     label=csv_name)

        return render(request, 'db_output/confirm_upload_details.html',
                      context={'csv_name': csv_name, 'game_details_form': game_details_form})

    elif request.method == 'POST':
        game_details_form = playerNameValidationForm(request.POST,choices=(['11','22'],['33','44']),
                                             label='default_label')
        if game_details_form.is_valid():

            print(str(game_details_form.cleaned_data))

            csv_name = request.session['player_list'].pop()

            name_choices = []
            for stored_player in Player.objects.all():
                if csv_name in stored_player.csv_names:
                    name_choices.append([stored_player, str(stored_player)])

            if not name_choices:
                name_choices.append(('no player', 'no player'))

            game_details_form = playerNameValidationForm(choices=name_choices,
                                                         label=csv_name)

            return render(request, 'db_output/confirm_upload_details.html',
                          {'csv_name': csv_name, 'game_details_form': game_details_form})



    else:
        raise AssertionError # shouldn't be here

    game_details_form = playerNameValidationForm(choices=(['testc1','testc2'],['samplec1','samplec2']),
                                                 label='this is a label')

    return render(request, 'db_output/confirm_upload_details.html',
                  context={'csv_name': csv_name, 'game_details_form': game_details_form})
