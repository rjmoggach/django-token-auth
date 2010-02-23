import time, datetime

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
from django.shortcuts import render_to_response, get_object_or_404

from forms import TokenForm, ForwardProtectedURLForm
from models import Token, ProtectedURL
from signals import signal_token_used


TOKEN_COOKIE = 'protectedurltokens'


def get_tokens_from_cookie(request):
    tokens = request.COOKIES.get(TOKEN_COOKIE, None)
    tokens_list = (tokens and tokens.split('|') or [])
    tokens_list = list(set(tokens_list))
    return tokens_list

def user_has_token_cookie(request, token=None):
    if not token is None:
        tokens = request.COOKIES.get(TOKEN_COOKIE, '')
        tokens_list = (tokens and tokens.split('|') or [])
        if token in tokens_list:
            return True
    return False


@login_required
def create_protected_url(request, **kwargs):
    kwargs['extra_context'] = {}
    if request.method == 'POST':
        form = TokenForm(request.POST)
        if form.is_valid():
            for email in form.cleaned_data['emails']:
                token = Token(
                    url=form.cleaned_data['url'],
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
                return HttpResponseRedirect(reverse('protected_url_created'))
    else:
        form = TokenForm(initial={'url': request.GET.get('url', '')})
    kwargs['extra_context']['form'] = form
    return direct_to_template(request, template='token_auth/create_protected_url.html', **kwargs)


def forward_token(request, token_str=None, **kwargs):
    kwargs['extra_context'] = {}
    error = None
    token = get_object_or_404(Token, token=token_str)
    user_tokens = get_tokens_from_cookie(request)
    if not token.can_forward:
        error = _("Apologies! This token can not be forwarded.")
    else:
        if request.user.is_staff:
            pass
        elif not token.token in user_tokens:
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
                    forwarded_token = Token( url=token.url, valid_until=token.valid_until, forward_count=0, email=email )
                    forwarded_token.save()
                    forwarded_token.send_token_email()
                return HttpResponseRedirect(reverse('protected_url_created'))
        else:
            form = ForwardProtectedURLForm(token)
        kwargs['extra_context']['form'] = form
    return direct_to_template(request, template='token_auth/forward_token.html', **kwargs)



def use_token_url(request, token_str=None, **kwargs):
    if not token_str is None:
        token = get_object_or_404(Token, token=token_str)
        # ok we have a token so let's start setting up the response
        response = HttpResponseRedirect(token.url)
        # if it's not used yet, set it as used
        if not token.used:
            response = HttpResponseRedirect(token.url)
            token.used = True
            token.save()
            signal_token_used.send(sender=use_token_url, request=request, token=token)
            max_age = 2592000
            expires_time = time.time() + max_age
            expires = cookie_date(expires_time)
            tokens_list = list(set(get_tokens_from_cookie(request) + [token.token]))
            tokens = '|'.join(tokens_list)
            response.set_cookie(TOKEN_COOKIE, tokens, max_age=max_age, expires=expires)
        # if token is used but user doesn't have token cookie so tell them NO
        elif not user_has_token_cookie(request, token=token.token):
            response = HttpResponseRedirect(reverse('token_url_used'))
        # cookie's expired... answer is still no
        elif not token.valid_until is None and token.valid_until <= datetime.datetime.now():
            response = HttpResponseRedirect(reverse('token_url_expired'))
        # user has a cookie with that token and it's still valid
        elif token.single_use:
            token.delete()
        return response
    else:
        return direct_to_template(request, template='token_auth/token_url_invalid.html', **kwargs)


def expire_token_url(request, token=None, **kwargs):
    max_age = 2592000
    expires_time = time.time() - max_age
    expires = cookie_date(expires_time)
    response = HttpResponseRedirect(reverse('token_url_expired'))
    response.set_cookie(TOKEN_COOKIE, '', max_age=max_age, expires=expires)
    return response


def token_url_used(request, template='token_auth/token_url_used.html', **kwargs):
    return direct_to_template(request, template, **kwargs)


def token_url_expired(request, template='token_auth/token_url_expired.html', **kwargs):
    return direct_to_template(request, template, **kwargs)


def token_url_invalid(request, template='token_auth/token_url_invalid.html', **kwargs):
    return direct_to_template(request, template, **kwargs)


def protected_url_created(request, template='token_auth/protected_url_created.html', **kwargs):
    return direct_to_template(request, template, **kwargs)
