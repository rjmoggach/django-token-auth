from datetime import datetime
from django.db.models import Manager

class ActiveTokenManager(Manager):
    """
    Manager for active tokens (not expired).
    """
    def get_query_set(self):
        queryset = super(ActiveTokenManager, self).get_query_set()
        return queryset.filter(valid_until__gte=datetime.now)
