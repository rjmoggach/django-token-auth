from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout, password_change, password_change_done
from django.contrib import admin


urlpatterns = patterns('',
    url('^create/((?P<url_id>\d+)/){0,1}$',
        'token_auth.views.create_token', name='create_token' ),
    url('^delete/(?P<url_id>\d+)/$',
        'token_auth.views.delete_protected_url', name='delete_protected_url'),
    url('^protect/$',
        'token_auth.views.protect_url', name='protect_url'),
    url('^list/$',
        'token_auth.views.token_list', name='token_list' ),
    url('^expired/$',
        'token_auth.views.expired_token_list', name='expired_token_list' ),
    url('^(?P<token_str>\w+)/$',
        'token_auth.views.use_token', name='use_token' ),
    url('^(?P<token_str>\w+)/forward/$',
        'token_auth.views.forward_token', name='forward_token' ),
    url('^(?P<token_str>\w+)/expire/$',
        'token_auth.views.expire_token', name='expire_token' ),
    url('^(?P<token_str>\w+)/delete/$',
        'token_auth.views.delete_token', name='delete_token' ),
    url('^(?P<token_str>\w+)/used/$',
        'token_auth.views.token_used', name='token_used' ),
    url('^(?P<token_str>\w+)/expired/$',
        'token_auth.views.token_expired', name='token_expired' ),
    url('^(?P<token_str>\w+)/invalid/$',
        'token_auth.views.token_invalid', name='token_invalid' ),
    url('^(?P<token_str>\w+)/send/$',
        'token_auth.views.send_email', name='send_email' ),
)
