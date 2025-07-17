from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import StepRecord, Group

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)

    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

class ManualStepEntryForm(forms.ModelForm):
    class Meta:
        model = StepRecord
        fields = ['step_count', 'timestamp']
        widgets = {
            'timestamp': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']