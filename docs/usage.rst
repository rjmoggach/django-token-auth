django-token-auth Usage
=========================

First thing you want to do is add ``token_auth`` to your
``INSTALLED_APPS`` and run::

    python manage.py syncdb
    
This will add the necessary tables.

Then add the following to your ``MIDDLEWARE_CLASSES``::

    token_auth.middleware.ProtectedURLsMiddleware


Protected URLs
-------------------------

#.  Use the admin interface to add Protected URLs. These URLs will
    be restricted to users that are authenticated or users that
    have clicked on the corresponding Protected URL Token.
#.  Create a token for the URL with the inline form or explicitly
    using the token admin form.
#.  From the Protected URL Token admin page select some tokens, and
    select the ``Send Token Email`` action to send emails to these users.
 
 
Autologin Middleware
-------------------------

This optional middleware allows your users to login by simply clicking
on a Token URL. It looks for a user with the email addressed associated
with a token and logs them in.

** Don't use this if security is a huge concern **

Add the following to your ``MIDDLEWARE_CLASSES``::

    token_auth.middleware.TokenAuthLoginMiddleware
