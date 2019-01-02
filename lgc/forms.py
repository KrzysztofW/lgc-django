from django import forms
from .models import Person

class PersonCreateForm(forms.ModelForm):
    passeport_expiry = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    work_authorization_start = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    work_authorization_end = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    residence_permit_start = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    residence_permit_end = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    birth_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))

    class Meta:
        model = Person
        exclude = ['creation_date']
