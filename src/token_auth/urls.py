from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url('^create/$',
        'token_auth.views.create_protected_url',
        name='protectedurl_create' ),
    url('^created/$',
        'django.views.generic.simple.direct_to_template',
        name='protectedurl_created',
        kwargs={'template': 'token_auth/protected_url_created.html'} ),
    url('^forward/(?P<token>\w+)/$',
        'token_auth.views.forward_protected_url',
        name='protectedurl_forward_token' ),
    url('^use/(?P<token>\w+)/$',
        'token_auth.views.use_token',
        name='protectedurl_use_token' ),
    url('^expire/(?P<token>\w+)/$',
        'token_auth.views.expire_token',
        name='protectedurl_expire_token' ),
    url('^protected/$',
        'django.views.generic.simple.direct_to_template',
        name='protectedurl_protected',
        kwargs={'template': 'token_auth/protected_url.html'} )
)
