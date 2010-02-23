from datetime import datetime

from django.db import models
from django.db.models import permalink
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from managers import ActiveTokenManager


class ProtectedURL(models.Model):
    """
    Model to identify protected URLs.
    """
    url = models.CharField(_('Protected URL'), max_length=255, unique=True)

    class Meta:
        verbose_name = _('Protected URL')
        verbose_name_plural = _('Protected URLs')

    def __unicode__(self):
        return u"%s" % self.url

    objects = models.Manager()


class Token(models.Model):
    """
    Model to store tokens related to individual urls and an email address.
    These tokens can expire and can optionally be forwarded by the user
    a definable number of times.
    """
    url = models.CharField(_('Allow URL'), max_length=255)
    name = models.CharField(_('Name'), max_length=64, blank=True, null=True)
    email = models.EmailField(_('Email Address'))
    token = models.CharField(_('URL Token'), max_length=20, editable=False)
    valid_until = models.DateTimeField(_('Valid Until'), null=True, blank=True)
    forward_count = models.PositiveIntegerField(_('Forward Count'), null=True, blank=True, default=0)
    used = models.BooleanField(_('Token Used?'), default=False)
    single_use = models.BooleanField(_('Single Use Token?'), default=False)


    objects = models.Manager()
    active_objects = ActiveTokenManager()


    class Meta:
        verbose_name = _('Protected URL Token')
        verbose_name_plural = _('Protected URL Tokens')
        ordering = ('email', '-used', '-valid_until', 'url')
    
    def __unicode__(self):
        return u"%s:%s - %s" % (self.email, self.url, self.token)
    
    def create_token(self):
        """
        Create a unique SHA token/hash using the project SECRET_KEY, URL,
        email address and current datetime.
        """
        from django.utils.hashcompat import sha_constructor
        hash = sha_constructor(settings.SECRET_KEY + self.url + self.email + unicode(datetime.now()) ).hexdigest()
        return hash[::2]

    """ if token doesn't exist create it on save """
    def save(self, **kwargs):
        if not self.pk:
            self.token = self.create_token()
        super(Token, self).save(**kwargs)
    
    def _forward_token_url(self):
        return ('forward_token_url', (), {'token_str': self.token})
    forward_token_url = permalink(_forward_token_url)
    
    def _use_token_url(self):
        return ('use_token_url', (), {'token_str': self.token})
    use_token_url = permalink(_use_token_url)

    """ make the url, token and associated email immutable """
    def __setattr__(self, name, value):
        if name in ['token', 'email', 'url']:
            if getattr(self, name, None): return
        super(Token, self).__setattr__(name, value)

    def _get_expired_boolean(self):
        """
        Returns ``True`` if the token has expired.
        """
        return self.valid_until is None or self.valid_until >= datetime.datetime.now()
    expired=property(_get_expired_boolean)

    def _get_forward_boolean(self):
        """
        Returns ``True`` if the token can be forwarded.
        """
        return self.forward_count is None or self.forward_count is not 0
    can_forward = property(_get_forward_boolean)

    def send_token_email(self, forwarded_by=None):
        subject = render_to_string('token_auth/token_email_subject.txt', { 'restricted_url': self.url } )
        subject = ''.join(subject.splitlines())
        message = render_to_string('token_auth/token_email_message.txt', { 'token': self, 'forwarded_by': forwarded_by } )
        if not settings.DEBUG:
            if not self.expired:
                EmailMessage(subject, message, [self.email] ).send()
