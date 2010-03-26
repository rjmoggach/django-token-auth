import time, datetime

from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
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

from forms import TokenAddForm, ForwardProtectedURLForm, ProtectedURLForm
from models import Token, ProtectedURL
from signals import signal_token_used, signal_token_visited


TOKEN_COOKIE = 'protectedurltokens'


def get_tokens_from_cookie(request):
    tokens = request.COOKIES.get(TOKEN_COOKIE, None)
    tokens_list = (tokens and tokens.split('|') or [])
    tokens_list = list(set(tokens_list))
    return tokens_list


def user_has_token_cookie(request, token_str=None):
    if not token_str is None:
        tokens = request.COOKIES.get(TOKEN_COOKIE, '')
        tokens_list = (tokens and tokens.split('|') or [])
        if token_str in tokens_list:
            return True
    return False


@user_passes_test(lambda u: u.has_perm('token_auth.add_token'))
def create_token(request, url_id=None, **kwargs):
    kwargs['extra_context'] = {}
    if request.method == 'POST':
        form = TokenAddForm(request.POST)
        if form.is_valid():
            email=form.cleaned_data['email']
            token = Token(
                url=form.cleaned_data['url'],
                valid_until=form.cleaned_data['valid_until'],
                forward_count=form.cleaned_data['forward_count'],
                email=email,
                name=form.cleaned_data['name'],
            )
            token.save()
            subject = render_to_string('token_auth/token_email_subject.txt', { 'token': token } )
            subject = ''.join(subject.splitlines())
            message = render_to_string('token_auth/token_email_message.txt', { 'token': token } )
            if settings.DEBUG:
                EmailMessage(subject=subject, body=message, to=(email,)).send()
            return HttpResponseRedirect(reverse('token_list'))
    else:
        initial_data = None
        if not url_id is None:
            url = ProtectedURL.objects.get(id=url_id)
            initial_data = {'url': url.url, }
        form = TokenAddForm( initial=initial_data )
    kwargs['extra_context']['form'] = form
    return direct_to_template(request, template='token_auth/create_token.html', **kwargs)


@user_passes_test(lambda u: u.has_perm('token_auth.add_protectedurl'))
def protect_url(request, **kwargs):
    kwargs['extra_context'] = {}
    if request.method == 'POST':
        form = ProtectedURLForm(request.POST)
        if form.is_valid():
            protected_url = ProtectedURL( url=form.cleaned_data['url'] )
            protected_url.save()
            return HttpResponseRedirect(reverse('token_list'))
    else:
        form = ProtectedURLForm()
    kwargs['extra_context']['form'] = form
    return direct_to_template(request, template='token_auth/protect_url.html', **kwargs)


@user_passes_test(lambda u: u.has_perm('token_auth.add_protectedurl'))
def delete_protected_url(request, url_id=None, **kwargs):
    try:
        url = ProtectedURL.objects.get(pk=url_id)
        url.delete()
    except:
        pass
    return HttpResponseRedirect(reverse('token_list'))
    

@user_passes_test(lambda u: u.has_perm('token_auth.add_protectedurl'))
def delete_token(request, token_str=None, **kwargs):
    try:
        token = Token.objects.get(token=token_str)
        token.delete()
    except:
        pass
    return HttpResponseRedirect(reverse('expired_token_list'))
    

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
                return HttpResponseRedirect(reverse('token_list'))
        else:
            form = ForwardProtectedURLForm(token)
        kwargs['extra_context']['form'] = form
    return direct_to_template(request, template='token_auth/forward_token.html', **kwargs)



def use_token(request, token_str=None, **kwargs):
    if not token_str is None:
        token = get_object_or_404(Token, token=token_str)
        response = HttpResponseRedirect(token.url)
        if not token.used:
            response = HttpResponseRedirect(token.url)
            token.used = True
            token.save()
            signal_token_used.send(sender=use_token, request=request, token=token)
            max_age = 2592000
            expires_time = time.time() + max_age
            expires = cookie_date(expires_time)
            tokens_list = list(set(get_tokens_from_cookie(request) + [token.token]))
            tokens = '|'.join(tokens_list)
            response.set_cookie(TOKEN_COOKIE, tokens, max_age=max_age, expires=expires)
        # if token is used but user doesn't have token cookie so tell them NO
        elif not user_has_token_cookie(request, token=token.token):
            response = HttpResponseRedirect(reverse('token_used', kwargs={'token_str':token.token,}))
        # cookie's expired... answer is still no
        elif not token.valid_until is None and token.valid_until <= datetime.datetime.now():
            response = HttpResponseRedirect(reverse('token_expired'))
        # user has a cookie with that token and it's still valid
        elif token.single_use:
            token.delete()
        signal_token_visited.send(sender=use_token, request=request, token=token)
        return response
    else:
        return direct_to_template(request, template='token_auth/token_invalid.html', **kwargs)


@user_passes_test(lambda u: u.has_perm('token_auth.add_token'))
def expire_token(request, token_str=None, **kwargs):
    response = HttpResponseRedirect(reverse('token_list'))
    if not token_str is None:
        max_age = 2592000
        expires_time = time.time() - max_age
        expires = cookie_date(expires_time)
        token = Token.objects.get(token__exact=token_str)
        token.valid_until = datetime.datetime.now()
        token.save()
        response.set_cookie(TOKEN_COOKIE, '', max_age=max_age, expires=expires)
    else:
        pass
    return response


def token_used(request, template='token_auth/token_used.html', token_str=None, **kwargs):
    if not token_str is None:
        extra_context={'token_str': token_str, }
    return direct_to_template(request, template, extra_context=extra_context, **kwargs)


def token_expired(request, template='token_auth/token_expired.html', token_str=None, **kwargs):
    if not token_str is None:
        extra_context={'token_str': token_str, }
    return direct_to_template(request, template, extra_context=extra_context, **kwargs)


def token_invalid(request, template='token_auth/token_invalid.html', token_str=None, **kwargs):
    if not token_str is None:
        extra_context={'token_str': token_str, }
    return direct_to_template(request, template, extra_context=extra_context, **kwargs)


@user_passes_test(lambda u: u.has_perm('token_auth.add_protectedurl'))
def token_list(request):
    url_list = ProtectedURL.objects.all()
    return list_detail.object_list(
        request,
        queryset = Token.active_objects.all().order_by('url'),
        template_name = 'token_auth/token_list.html',
        template_object_name = 'token',
        allow_empty = True,
        extra_context = {'url_list': url_list, }
        )

@user_passes_test(lambda u: u.has_perm('token_auth.add_protectedurl'))
def expired_token_list(request):
    return list_detail.object_list(
        request,
        queryset = Token.expired_objects.all().order_by('url'),
        template_name = 'token_auth/expired_token_list.html',
        template_object_name = 'token',
        allow_empty = True,
        )
