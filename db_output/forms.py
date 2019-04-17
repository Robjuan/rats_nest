from django import forms
from django_select2.forms import ModelSelect2MultipleWidget, ModelSelect2Widget
from .models import csvDocument, Team, Player, Game
from django.forms.widgets import DateInput


class csvDocumentForm(forms.ModelForm):
    # TODO: upload controls

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


# TODO (lp): restrict access to test data
def get_primary_validation_form(param_model, field):
    import logging
    logger = logging.getLogger(__name__)

    class PrimaryValidationForm(forms.ModelForm):
        selected = forms.BooleanField(required=False,
                                      initial=False,
                                      label='Use Custom '+str(param_model.__name__)+"?")

        def __init__(self, *args, **kwargs):
            if 'prefix' not in kwargs:  # formsets will use prefix in kwargs
                self.prefix = 'primary_validator'
            super().__init__(*args, **kwargs)
            for field_name, _field in self.fields.items():
                _field.widget.attrs['data-modeltype'] = str(param_model.__name__)

        class Meta:
            model = param_model
            fields = ('selected', field,)
            widgets = {field: ModelSelect2Widget(
                label='Search by ' + str(field),
                model=param_model,
                search_fields=[field + '__icontains'],
                attrs={'data-width': '75%'},
            )
            }

    return PrimaryValidationForm


def get_secondary_validation_form(param_model):
    import logging
    logger = logging.getLogger(__name__)

    class SecondaryValidationForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            if 'prefix' not in kwargs:
                self.prefix = 'secondary_validator'
            super().__init__(*args, **kwargs)
            for field_name, _field in self.fields.items():
                _field.widget.attrs['data-modeltype'] = str(param_model.__name__)


        class Meta:
            model = param_model
            if param_model == Team:
                exclude = ('players',)
                # Team is done individually, so modelformset will not forcibly rendering the pk field
                # AutoFields are not displayable manually
                # However, we can fetch the selected pk from the select2 box using javascript

            elif param_model == Player:
                # player_ID is excluded because we do not want to render it
                # however, a modelformset requires it and will forcibly render it as a hidden field
                # this is good because we actually need it to save the player pk (without using js)
                exclude = ('player_ID', 'csv_names')
                widgets = {'dob': DateInput(attrs={'type': 'date'})}  # might not work in FF or Safari?

    return SecondaryValidationForm


class AnalysisForm(forms.Form):

    # TODO: restrict to teams with games
    team = forms.ModelChoiceField(
        queryset=Team.objects.with_games(),
        label="Team",
        widget=ModelSelect2Widget(
            model=Team,
            search_fields=['team_name__icontains'],
            attrs={'data-width': '75%',  # resolve is giving me 35px whether explicit or implicit
                   'data-modeltype': 'Team'},

        )
    )

    # TODO: filter out non-verified data here
    games = forms.ModelMultipleChoiceField(
        # queryset=Game.objects.all(),
        queryset=Game.objects.filter(verified=True),
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

