import datetime
import sys

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth import login, get_backends

from views import get_tokens_from_cookie
from signals import signal_token_visited
from models import ProtectedURL, TokenURL


class ProtectedURLMiddleware(object):
    """
    This middleware requires a login or associated token for protected urls.
    """

    def check_for_user_or_token(self, request):
        # check user is not anonymous and is logged in
        if not isinstance(request.user, AnonymousUser) and request.user.is_authenticated():
            return True
        # see if a protected url token exists
        if getattr(request, 'valid_token', None):
            return True
        return False
    
    def process_request(self, request):
        if not request.path is '/':
            where_sql = 'SUBSTR("%s", 1, LENGTH(url)) = url' % (request.path)
            if ProtectedURL.objects.extra(where=[where_sql]):
                user_tokens = get_tokens_from_cookie(request) # get the user's tokens
                tokens = TokenURL.active_objects.filter(token__in=user_tokens).order_by('url__url').select_related('url')
                if tokens:
                    for token in tokens:
                        if request.path.startswith(token.url.url):
                            signal_token_visited.send(sender=self.__class__, request=request, token=token)
                            request.valid_token = token
                            break
                allowed = self.check_for_user_or_token(request)
                if not allowed:
                    return HttpResponseRedirect(reverse('login_form'))
        else:
            if ProtectedURL.objects.get(url='/'):
                user_tokens = get_tokens_from_cookie(request) # get the user's tokens
                tokens = TokenURL.active_objects.filter(token__in=user_tokens,url__url__exact='/')
                if tokens:
                    request.valid_token = tokens[0]
                allowed = self.check_for_user_or_token(request)
                if not allowed:
                    return HttpResponseRedirect(reverse('login_form'))
        

class TokenAuthLoginMiddleware(object):
    def process_request(self, request):
        if isinstance(request.user, AnonymousUser):
            token_str = getattr(request, 'token_str', None)
            user_tokens = get_tokens_from_cookie(request)
            # this is a security risk but at least require a cookie so we get close
            if not token_str is None and token_str in user_tokens:
                token = get_object_or_404(TokenURL, token=token_str)
                try:
                    user = User.objects.get(email=token.email)
                    backend = get_backends()[0]
                    user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
                    login(request, user)
                except:
                    pass
