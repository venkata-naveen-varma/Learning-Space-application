from django import forms
from .models import Notes

class DocumentForm(forms.ModelForm):
    """ To upload a file """
    class Meta:
        model = Notes
        fields = ('name', 'content', 'notes_doc')
