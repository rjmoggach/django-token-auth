from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from models import ProtectedURL, Token
from views import forward_token
from forms import TokenAddForm


class TokenInline(admin.TabularInline):
    model = Token
    form = TokenAddForm
    extra = 1


class ProtectedURLAdmin(admin.ModelAdmin):
    #    inlines = [TokenInline, ]
    list_display = ('url', )
admin.site.register(ProtectedURL, ProtectedURLAdmin)


class TokenAdmin(admin.ModelAdmin):
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
            if not token.expired: forward_token(token)
    send_token_email.short_description = _("Send token email(s).")
admin.site.register(Token, TokenAdmin)
