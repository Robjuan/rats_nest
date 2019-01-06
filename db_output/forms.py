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
        ('provided','provided'),
        ('custom','custom')
    )

    selection = forms.ChoiceField(
        choices=choices, widget=forms.RadioSelect)
    custom_name = forms.CharField(
        label="", required=False)

    def __init__(self, data=None, *args, **kwargs):
        if 'choices' in kwargs:
            choices = kwargs.pop('choices')
            self.fields['custom_name'].choices = choices

        super(ValidationForm, self).__init__(data, *args, **kwargs)

        # If 'later' is chosen, set send_date as required
        if data and data.get('selection', None) == 'custom':
            self.fields['custom_name'].required = True
