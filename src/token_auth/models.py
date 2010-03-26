from datetime import datetime

from django.db import models
from django.db.models import permalink
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from managers import ActiveTokenManager, ExpiredTokenManager
from signals import signal_token_visited

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
    description = models.CharField(_('Description'), max_length=128, blank=True, null=True)
    email = models.EmailField(_('Email Address'))
    token = models.CharField(_('URL Token'), max_length=20, editable=False)
    valid_until = models.DateTimeField(_('Valid Until'), null=True, blank=True)
    forward_count = models.PositiveIntegerField(_('Forward Count'), null=True, blank=True, default=0)
    used = models.BooleanField(_('Token Used?'), default=False)
    single_use = models.BooleanField(_('Single Use Token?'), default=False)
    page_views = models.IntegerField(_('Page Views'), default=0)
    

    objects = models.Manager()
    active_objects = ActiveTokenManager()
    expired_objects = ExpiredTokenManager()


    class Meta:
        verbose_name = _('Protected URL Token')
        verbose_name_plural = _('Protected URL Tokens')
        ordering = ('email', '-used', '-valid_until', 'url')
    
    def __unicode__(self):
        return u"%s:%s - %s" % (self.email, self.url, self.token)
    
    def generate_hash(self):
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
            self.token = self.generate_hash()
        super(Token, self).save(**kwargs)
    
    def _forward_token(self):
        return ('forward_token', (), {'token_str': self.token})
    forward_token = permalink(_forward_token)
    
    def _use_token(self):
        return ('use_token', (), {'token_str': self.token})
    use_token = permalink(_use_token)

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
        return not self.forward_count in (None, 0)
    can_forward = property(_get_forward_boolean)

    def send_token_email(self, forwarded_by=None):
        subject = render_to_string('token_auth/token_email_subject.txt', { 'restricted_url': self.url } )
        subject = ''.join(subject.splitlines())
        message = render_to_string('token_auth/token_email_message.txt', { 'token': self, 'forwarded_by': forwarded_by } )
        if not settings.DEBUG:
            if not self.expired:
                EmailMessage(subject, message, [self.email] ).send()
    
    def viewed(self):
        self.page_views += 1
        self.save()


def increment_page_views(sender, **kwargs):
    token=kwargs['token']
    token.viewed()
signal_token_visited.connect(increment_page_views)