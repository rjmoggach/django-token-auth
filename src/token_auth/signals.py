import django.dispatch


""" Signal when a token is used (link in email is visited)"""
signal_token_used = django.dispatch.Signal(providing_args=["request", "token"])


""" Signal when a url with token a is visited (the url the token is connected to)"""
signal_token_visited = django.dispatch.Signal(providing_args=["request", "token"])

