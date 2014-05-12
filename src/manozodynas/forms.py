from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput(render_value=None))

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        if self.errors:
            return cleaned_data

        user = authenticate(**cleaned_data)
        if not user:
            raise forms.ValidationError(_('Username or password is incorrect'))
        cleaned_data['user'] = user
        return cleaned_data