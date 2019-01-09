from django import forms

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



class ValidationForm(forms.Form):

    choices = (
        ('provided', 'no match, custom will be used'),
        ('custom', 'custom')
    )

    selection = forms.ChoiceField(
        choices=choices, widget=forms.RadioSelect)
    custom_name = forms.CharField(
        label="", required=False)

    def __init__(self, data=None, *args, **kwargs):
        if 'match' in kwargs:
            match = kwargs.pop('match')
        else:
            match = None

        super(ValidationForm, self).__init__(data, *args, **kwargs)

        if match:
            self.fields['selection'].choices = (('provided', match), ('custom', 'custom'))

        # charfield only NOT required if both a valid match avail, and that match is picked
        if data and data.get('selection', None) == 'custom':
            self.fields['custom_name'].required = True
        if not match:
            self.fields['custom_name'].required = True
