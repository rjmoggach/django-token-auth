===================
Django Token Auth
===================

written by fivethreeo_ and mogga_

.. _fivethreeo: http://github.com/fivethreeo/
.. _mogga: http://github.com/mogga/

``django-token-auth`` is a generic, reusable app to restrict access
to selected URLs or optionally allow auto-authentication upon
clicking a unique token/hash URL.
 
Predicted Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~

#. A form asks for a URL and a list of emails 
#. You enter the URL to secure, a few emails separated by carriage returns, and hit submit 
#. A hash URL is generated for each email and messages are sent 
#. Clicking on the hash URL creates the cookie and redirects the user to the 'secure' page 
#. Any requests/responses for the 'secure' page are caught by middleware that checks for the cookie 
#. After first visit cookie generation is optionally disabled to prevent forwarding 

Other Features
~~~~~~~~~~~~~~~~~~~~~~~~~~

* user is optionally able to forward the link to other emails
* token is optionally disabled after first click through to prevent forwarding
* click throughs and page views can be trackable per hash URL via built-in signals
* access can expire
* sub-URL access is also restricted /cool/new/tech/version_A etc. 
* includes optional middleware to automatically authenticate existing user

Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~

Restrict Access
--------------------------

We want to restrict direct access to the following URL
for visitors without a cookie:

    **http://mysite.com/cool/new/tech/**

We want to allow access to user(s) who click on a URL
like the following:

    **http://mysite.com/private/zpwhtygjntrz**

Clicking on the link generates a cookie that allows
access and redirects the user to the protected URL.

Easy Authorization
--------------------------

Some users need to be treated gently like the luddites they are.
Send them a link like the following:

    **http://mysite.com/auth/zpwhtygjntrz**

...and they're logged in automagically. This is an obvious security risk
but great for client sites where security is necessary but not
overbearing.

