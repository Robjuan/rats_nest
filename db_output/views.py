from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

# only required for method 2 , simple saving
from django.core.files.storage import default_storage


def index(request):

    return HttpResponse(render(request, 'db_output/index.html', {}))


def test_output(request):

    from .ua_parser import parse

    display_txt = parse()

    return HttpResponse('this is produced by the parse() function<p>' +
                        str(display_txt))


def insert_test_data(request):

    from .models import Players
    p = Players(proper_name='homer simpson', hometown='evergreen terrace')
    p.save()

    # print(Players.objects.all())

    return HttpResponse('You have inserted '+str(p))


# the first time you go to a view, it will be with request.method = 'GET'
# after you click submit, you will be sent back to that page with request.method = 'POST'
# the form is then filled from the data which is now in the request and handled as you see fit


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
