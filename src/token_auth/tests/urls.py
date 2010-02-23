from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url('^token_auth/',
        include('token_auth.urls')
    ),
    
    url('^protected/$',
        'token_auth.tests.views.example'
    ),
    url('^protected/sub1/$',
        'token_auth.tests.views.example'
    ),
    url('^protected/sub1/sub2/$',
        'token_auth.tests.views.example'
    ),
    url('^login/$',
        'token_auth.tests.views.example',
        name='login_form'
    )
    
)
