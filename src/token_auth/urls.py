from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout, password_change, password_change_done
from django.contrib import admin


urlpatterns = patterns('',
    url('^create/$',
        'token_auth.views.create_protected_url', name='create_protected_url' ),
    url('^created/$',
        'token_auth.views.protected_url_created', name='protected_url_created'),
    url('^(?P<token_str>\w+)/$',
        'token_auth.views.use_token_url', name='use_token_url' ),
    url('^(?P<token_str>\w+)/forward/$',
        'token_auth.views.forward_token', name='forward_token_url' ),
    url('^(?P<token_str>\w+)/expire/$',
        'token_auth.views.expire_token_url', name='expire_token_url' ),
    url('^(?P<token_str>\w+)/used/$',
        'token_auth.views.token_url_used', name='token_url_used' ),
    url('^(?P<token_str>\w+)/expired/$',
        'token_auth.views.token_url_expired', name='token_url_expired' ),
    url('^(?P<token_str>\w+)/invalid/$',
        'token_auth.views.token_url_invalid', name='token_url_invalid' ),
)
