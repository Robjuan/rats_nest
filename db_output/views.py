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

    # print(request.session['player_list'])
    # appears to be the same (full) list every time we come here

    csv_name = request.session['player_list'].pop()

    name_choices = []
    for stored_player in Player.objects.all():
        if csv_name in stored_player.csv_names:
            name_choices.append([stored_player, str(stored_player)])

    if not name_choices:
        name_choices.append(('no match', 'no match'))

    name_validation_form = ValidationForm()

    if request.method == 'POST':
        name_validation_form = ValidationForm(request.POST)
        if name_validation_form.is_valid():
            results = name_validation_form.cleaned_data

            return render(request, 'db_output/confirm_upload_details.html',
                          context={'form': name_validation_form, 'csv_name': csv_name, 'results': results})


    return render(request, 'db_output/confirm_upload_details.html',
                      context={'form': name_validation_form, 'csv_name': csv_name})
