from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

# only required for method 2 , simple saving
from django.core.files.storage import default_storage


def index(request):

    return HttpResponse(render(request, 'db_output/index.html', {}))


def test_output(request):

    from .ua_parser import parse, get_player_names
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
            request.session['player_list'] = get_player_names(filename)

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
    # TODO: if there are no more players to confirm, this should bounce us out to a confirmation view
    if not player_list:
        return HttpResponseRedirect('/')

    csv_name = player_list.pop()  # calling pop directly on session doesn't work - this does
    request.session['player_list'] = player_list

    match = None
    for stored_player in Player.objects.all():
        if csv_name in stored_player.csv_names:
            match = str(stored_player)

    name_validation_form = ValidationForm(match=match)

    if request.method == 'POST':
        name_validation_form = ValidationForm(request.POST, match=match)
        if name_validation_form.is_valid():
            results = name_validation_form.cleaned_data

            # conversion dict will be { csv_name : actual_player_pk }
            new_dict = request.session['conversion_dict']

            if results['selection'] == 'provided':
                # find player object based on match, put in pk
                new_dict[csv_name] = stored_player.player_ID
                stored_player.csv_names.append(','+csv_name)

            elif results['selection'] == 'custom':
                # create new Player, input Proper name as given and csv_name as csv_name
                given_name = results['custom_name']
                new_player = Player(proper_name=given_name, csv_names=csv_name)
                new_dict[csv_name] = new_player.player_ID

            request.session['conversion_dict'] = new_dict
            return render(request, 'db_output/confirm_upload_details.html',
                          context={'form': name_validation_form, 'csv_name': csv_name, 'results': results})
    else:
        request.session['conversion_dict'] = {}
        return render(request, 'db_output/confirm_upload_details.html',
                  context={'form': name_validation_form, 'csv_name': csv_name})


def confirm_conversion_dict(request):

    # TODO: handle confirm/cancel buttons
    # cancel can just bounce them back to test_output
    # confirm can send them to parse!!!!!!!!

    if request.method == 'POST':
        return HttpResponseRedirect('display_parse_results')
    else:
        content = request.session['conversion_dict']
        return render(request, 'db_output/base.html', context={'content':content})


def display_parse_results(request):

    from .ua_parser import parse

    content = parse(request.session['filename'], request.session['conversion_dict'])
    # currently this just gives us a success indicating string


    return render(request, 'db_output/base.html', context={'content':content})
