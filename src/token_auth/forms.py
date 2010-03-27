from django import forms
from models import Token, ProtectedURL

        
class TokenAddForm(forms.ModelForm):
    class Meta:
        model = Token
        fields = ('url', 'name', 'email', 'description', 'forward_count', 'valid_until')

class ProtectedURLForm(forms.ModelForm):
    class Meta:
        model = ProtectedURL
    def clean_url(self):
        url = self.cleaned_data['url']
        if not url[0] is '/':
            url = '/%s' % url
        return url

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
