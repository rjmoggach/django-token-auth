from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from models import ProtectedURL, TokenURL
from views import forward_protected_url
from forms import TokenURLAddForm


class TokenURLInline(admin.TabularInline):
    model = TokenURL
    form = TokenURLAddForm
    extra = 1


class ProtectedURLAdmin(admin.ModelAdmin):
    #    inlines = [TokenURLInline, ]
    list_display = ('url', )
admin.site.register(ProtectedURL, ProtectedURLAdmin)


class TokenURLAdmin(admin.ModelAdmin):
    actions = ['send_token_email', ]
    list_display = ('email', 'url', 'token', 'valid_until', 'used')
    fieldsets = (
        (None, {
            'fields': (('url', 'valid_until')),
            'description': _('Create or select a url to protect and optionally set an expiration date.')
        }),
        (_('Visitor Information'), {
            'fields': (('name', 'email'), 'forward_count'),
            'description': _('Enter a name and email for the person you want to associate with this token and how many times they can forward it.')
        })
    )

    def send_token_email(self, request, queryset):
        """
        Sends token email(s) for the selected users.

        """
        for token in queryset:
            if not token.expired: forward_protected_url(token)
    send_token_email.short_description = _("Send token email(s).")
admin.site.register(TokenURL, TokenURLAdmin)
