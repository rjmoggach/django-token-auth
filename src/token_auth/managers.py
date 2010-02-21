from datetime import datetime
from django.db.models import Manager, Q


class ActiveTokenManager(Manager):
    """
    Manager for active tokens (not expired).
    """
    def get_query_set(self):
        queryset = super(ActiveTokenManager, self).get_query_set()
        return queryset.filter(Q(valid_until__isnull=True) | Q(valid_until__gte=datetime.now))
