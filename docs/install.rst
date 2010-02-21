Installing django-token-auth
============================

If you want to get the full buildout so you can bootstrap and check it out
locally in an isolated environment:

    git clone git://github.com/mogga/django-token-auth.git::

Then from within the base directory:

::    
    python bootstrap.py
    bin/buildout
    bin/runtests

If you want to install the package using pip:

    pip install -e git+git://github.com/mogga/django-token-auth.git#egg=django-token-auth::

Or the classic method, run the following command inside this directory:

    python setup.py install::

Or if you'd prefer you can simply place the included ``token_auth``
directory (within the src directory) somewhere on your Python path,
or symlink to it from somewhere on your Python path; this is useful if
you're working from a repository checkout.

Finally add ``token_auth`` to you ``INSTALLED_APPS`` and 
``token_auth.middleware.ProtectedURLsMiddleware`` to your ``MIDDLEWARE_CLASSES``.

Optionally add ``token_auth.middleware.TokenAuthLoginMiddleware``
to your ``MIDDLEWARE_CLASSES`` as well. Be warned this might present
a security risk.

Note that this application requires Python 2.4 or later, and a
functional installation of Django 1.0 or newer. You can obtain
Python from `www.python.org <http://www.python.org>`_ and
Django from `www.djangoproject.com <http://www.djangoproject.com>`_.
