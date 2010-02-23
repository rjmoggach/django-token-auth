from django import forms
from models import Token


class TokenForm(forms.Form):
    url = forms.CharField(max_length=255)
    valid_until = forms.DateField(required=False)
    emails = forms.CharField(max_length=255)
    forward_count = forms.IntegerField(required=False)
    
    def clean_emails(self):
        emails = self.cleaned_data['emails'].split(';')
        return emails

        
class TokenAddForm(forms.ModelForm):
    class Meta:
        model = Token
        fields = ('name', 'email', 'forward_count')


class ForwardProtectedURLForm(forms.Form):
    def __init__(self, token, *args, **kwargs):
        super(ForwardProtectedURLForm, self).__init__(*args, **kwargs)
        self.token = token
    
    emails = forms.CharField(max_length=255)
    
    def clean_emails(self):
        emails = self.cleaned_data['emails'].split(';')
        if self.token.forward_count and len(emails) > self.token.forward_count:
                raise forms.ValidationError("You can only forward to %i emails." % (self.token.forward_count or 0))
        return emails
