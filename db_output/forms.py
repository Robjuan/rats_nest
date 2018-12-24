from django import forms
from .xorformfields.forms import MutuallyExclusiveValueField, MutuallyExclusiveRadioWidget

from .models import csvDocument


class csvDocumentForm(forms.ModelForm):
    class Meta:
        model = csvDocument
        fields = ('your_team_name', 'description', 'file')


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


class playerNameValidationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'choices' in kwargs:
            choices = kwargs.pop('choices')
        else:
            choices = (['default','default'],['default','default'])

        if 'label' in kwargs:
            label = kwargs.pop('label')

        super(playerNameValidationForm, self).__init__(*args, **kwargs)

        xor_fields = MutuallyExclusiveValueField(
            fields=(forms.CharField(), forms.CharField()),
            widget=MutuallyExclusiveRadioWidget(widgets=(
                forms.Select(choices=choices),
                forms.TextInput(),  # TODO: give this a default value or make it not required (pref 2nd)
            )))

        if label:
            xor_fields.label = label

        self.fields['xor_fields'] = xor_fields


class testNameValidationForm(forms.Form):
    csv_name = MutuallyExclusiveValueField(
        fields=(forms.CharField(), forms.CharField()),
        widget=MutuallyExclusiveRadioWidget(widgets=(
            forms.Select(choices=(['1','2'],['4','5'])),
            forms.TextInput(),
        )))
