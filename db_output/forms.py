from django import forms
from .models import csvDocument


class csvDocumentForm(forms.ModelForm):
    class Meta:
        model = csvDocument
        fields = ('your_team_name', 'description', 'file')


class fileSelector(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super().__init__(*args, **kwargs)
        self.fields['filechoice'] = forms.ChoiceField(label='Select File', choices=choices)
