"""
Views which allow:
    * authenticated users to create protected URL
    * token authenticated users to forward protected URLs
    * forwarding from token URL to protected URL

"""
import time
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.http import cookie_date
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ugettext_lazy as _

from token_auth.forms import ProtectedURLTokenForm, ForwardProtectedURLForm
from token_auth.models import TokenURL, ProtectedURLToken
from token_auth.signals import token_used


@login_required
def create_protected_url(request, **kwargs):
    kwargs['extra_context'] = {}
    if request.method == 'POST':
        form = ProtectedURLTokenForm(request.POST)
        if form.is_valid():
            url, created = TokenURL.objects.get_or_create(url=form.cleaned_data['url'])
            for email in form.cleaned_data['emails']:
                token = ProtectedURLToken(
                    url=url,
                    valid_until=form.cleaned_data['valid_until'],
                    forward_count=form.cleaned_data['forward_count'],
                    email=email
                )
                token.save()
                subject = render_to_string('token_auth/token_email_subject.txt', { 'token': token } )
                subject = ''.join(subject.splitlines())
                message = render_to_string('token_auth/token_email_message.txt', { 'token': token } )
                if not settings.DEBUG:
                    EmailMessage(subject, message, [email] ).send()
                return HttpResponseRedirect(reverse('protectedurl_created'))
    else:
        form = ProtectedURLTokenForm(initial={'url': request.GET.get('url', '')})
    kwargs['extra_context']['form'] = form
    return direct_to_template(request, template='token_auth/create_protected_url.html', **kwargs)
    

def forward_protected_url(request, token=None, **kwargs):
    kwargs['extra_context'] = {}
    error = None
    try:
        token = ProtectedURLToken.objects.get(token=token)
    except ProtectedURLToken.DoesNotExist:
        token = None
        error = "No such token"
    if token and not token.can_forward or (not isinstance(request.user, AnonymousUser) and request.user.is_authenticated()):
        error = _("Apologies! You are not allowed to forward this token.")
    kwargs['extra_context']['token'] = token
    kwargs['extra_context']['error'] = error
    if not error:        
        if request.method == 'POST':
            form = ForwardProtectedURLForm(token, request.POST)
            if form.is_valid():
                if token.forward_count:
                    token.forward_count = token.forward_count - len(form.cleaned_data['emails'])
                    token.save()
                for email in form.cleaned_data['emails']:
                    forwarded_token = ProtectedURLToken( url=token.url, valid_until=token.valid_until, forward_count=0, email=email )
                    forwarded_token.save()
                    forwarded_token.send_token_email()
                return HttpResponseRedirect(reverse('protectedurl_created'))
        else:        
            form = ForwardProtectedURLForm(token)
        kwargs['extra_context']['form'] = form
    return direct_to_template(request, template='token_auth/forward_protected_url.html', **kwargs)


def use_token(request, token=None, **kwargs):
    if token:
        try:
            token = ProtectedURLToken.objects.get(token=token)
        except ProtectedURLToken.DoesNotExist:
            token = None
        if not token is None:
            if token.used and settings.PROTECTEDURL_GENERATE_COOKIE_ONCE:
                kwargs['extra_context'] = {'token_used': True}
                return direct_to_template(request, template='token_auth/token_used.html', **kwargs)
            token.used = True
            token.save()
            token_used.send(sender=use_token, request=request, token=token)
            response = HttpResponseRedirect(token.url.url)
            max_age = 2592000
            expires_time = time.time() + max_age
            expires = cookie_date(expires_time)
            tokens = request.COOKIES.get('protectedurltokens', '')            
            tokens_list = (tokens and tokens.split('|') or []) + [token.token]
            tokens = '|'.join(list(set(tokens_list)))
            response.set_cookie('protectedurltokens', tokens, max_age=max_age, expires=expires)
            return response
    return direct_to_template(request, template='token_auth/token_invalid.html', **kwargs)
    
def expire_token(request, token=None, **kwargs):
    max_age = 2592000
    expires_time = time.time() - max_age
    expires = cookie_date(expires_time)
    response = HttpResponseRedirect(reverse('protextedurl_expired'))
    response.set_cookie('protectedurltokens', '', max_age=max_age, expires=expires)
    return response
            