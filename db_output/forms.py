from django import forms
from django_select2.forms import ModelSelect2MultipleWidget, ModelSelect2Widget
from django.core.validators import FileExtensionValidator
from .models import csvDocument, Team


class csvDocumentForm(forms.ModelForm):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['file'].validators = [FileExtensionValidator('.csv')]
    #     # django says to not rely on this because shit can be renamed
    #     # fair cop TODO: upload controls

    class Meta:
        model = csvDocument
        fields = ('your_team_name', 'season', 'description', 'file')


class fileSelector(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        if 'selected' in kwargs:
            selected = kwargs.pop('selected')
        else:
            selected = None

        super().__init__(*args, **kwargs)
        self.fields['filechoice'] = forms.ChoiceField(label='Select File', choices=choices)

        if selected:
            self.initial = selected


class TeamValidationForm(forms.ModelForm):
    class Meta:
        model = Team
        exclude = ('team_id', 'players')


class ValidationForm(forms.Form):

    choices = (
        ('provided', 'no match found, please provide custom name'),
        ('custom', 'custom')
    )

    selection = forms.ChoiceField(
        choices=choices, widget=forms.RadioSelect)
    custom_name = forms.CharField(
        label="", required=False)

    def __init__(self, data=None, *args, **kwargs):
        if 'match' in kwargs:
            self.match = kwargs.pop('match')
            if self.match == 'None':
                self.match = None  # this feels not pythonic
        else:
            self.match = None

        super(ValidationForm, self).__init__(data, *args, **kwargs)

        if self.match:
            self.fields['selection'].choices = (('provided', self.match), ('custom', 'custom'))

        # charfield only NOT required if both a valid match avail, and that match is picked
        if data and data.get('selection', None) == 'custom':
            self.fields['custom_name'].required = True
        if not self.match:
            self.fields['custom_name'].required = True

    def get_match(self):
        # match isn't part of cleaned_data but we still want to know if one exists
        # 20/1/18 is this being used anywhere?
        return self.match


class AnalysisForm(forms.Form):
    from .models import Team, Game

    team = forms.ModelChoiceField(
        queryset=Team.objects.all(),
        label="Team",
        widget=ModelSelect2Widget(
            model=Team,
            search_fields=['team_name__icontains'],
            attrs={'data-width': '75%'},  # resolve is giving me 35px whether explicit or implicit

        )
    )

    games = forms.ModelMultipleChoiceField(
        queryset=Game.objects.all(),
        label="Game(s)",
        widget=ModelSelect2MultipleWidget(
            model=Game,
            search_fields=['tournament_name'],
            dependent_fields={'team': 'team'},
            max_results=500,
            attrs={'data-width': '75%'},

        )
    )

    def __init__(self, *args, **kwargs):
        analysis_choices = kwargs.pop('analysis_choices')
        super().__init__(*args,**kwargs)
        self.fields['analysischoice'] = forms.MultipleChoiceField(choices=analysis_choices,
                                                                  widget=forms.CheckboxSelectMultiple)


class VerifyConfirmForm(forms.Form):
    verify = forms.BooleanField(required=False)

