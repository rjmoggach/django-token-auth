from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
import datetime

from token_auth.models import ProtectedURL, Token
from token_auth.views import TOKEN_COOKIE

EMAILS = 'test@test.com;test2@test.com'

FORM_DATA_URL_1 = { 'url': '/protected/', 'valid_until': '', 'emails': EMAILS }
FORM_DATA_URL_2 = { 'url': '/protected/sub1/', 'valid_until': '', 'emails': EMAILS }
FORM_DATA_URL_3 = { 'url': '/protected/sub1/sub2/', 'valid_until': '', 'emails': EMAILS }

FORM_DATA_FORWARD_1 = { 'emails': EMAILS }
FORM_DATA_FORWARD_2 = { 'emails': 'test@test.com' }


class TestURLs(TestCase):

    urls = 'token_auth.tests.urls'

    fixtures = ['test_fixtures.json']


    def setUp(self):
        url = ProtectedURL.objects.create(url='/protected/')


    def login(self, client, password='password'):
        login = client.login(username='token_auth', password=password)
        self.failUnless(login, 'Could not log in')


    def testAddURL(self):

        client = Client()

        response = client.get(reverse('create_protected_url'))
        self.failUnlessEqual(response.status_code, 302)

        self.login(client)

        response = client.get(reverse('create_protected_url'))

        self.failUnlessEqual(response.status_code, 200)
        self.failUnless(response, "no form in context")
        self.failUnlessEqual(response.context['form'].errors, {})

        response = client.post(reverse('create_protected_url'), FORM_DATA_URL_1)
        self.failUnlessEqual(response.status_code, 302)

        response = client.post(reverse('create_protected_url'), FORM_DATA_URL_2)
        self.failUnlessEqual(response.status_code, 302)

        response = client.post(reverse('create_protected_url'), FORM_DATA_URL_3)
        self.failUnlessEqual(response.status_code, 302)


    def testVisitURL302(self):

        client = Client()
        
        # test that protection works
        
        response = client.get('/protected/')
        self.failUnlessEqual(response.status_code, 302)

        response = client.get('/protected/sub1/')
        self.failUnlessEqual(response.status_code, 302)

        response = client.get('/protected/sub1/sub2/')
        self.failUnlessEqual(response.status_code, 302)


    def testVisitURL200Cookie(self):

        url = '/protected/'

        token = Token(url=url)
        token.save()

        client = Client()

        # test that tokens work
        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)
        self.failUnlessEqual(client.cookies[TOKEN_COOKIE].value, token.token)

        response = client.get("/protected/")
        self.failUnlessEqual(response.status_code, 200)

        response = client.get("/protected/sub1/")
        self.failUnlessEqual(response.status_code, 200)

        response = client.get("/protected/sub1/sub2/")
        self.failUnlessEqual(response.status_code, 200)

        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)

        # test for two tokens
        token2 = Token(url=url)
        token2.save()

        response = client.get(token2.use_token_url())
        self.failUnlessEqual(response.status_code, 302)
        self.failUnless(client.cookies[TOKEN_COOKIE].value, token.token + '|' + token2.token)

        token.delete()
        token2.delete()

        # test for expired tokens
        token3 = Token(url=url)
        token3.save()

        response = client.get(token3.use_token_url())
        self.failUnlessEqual(response.status_code, 302)

        response = client.get("/protected/")
        self.failUnlessEqual(response.status_code, 200)

        token3.valid_until = datetime.datetime.today() - datetime.timedelta(days=2)
        token3.save()

        response = client.get("/protected/")
        self.failUnlessEqual(response.status_code, 302)


    def testVisitURL200User(self):

        client = Client()

        self.login(client)

        response = client.get('/protected/')
        self.failUnlessEqual(response.status_code, 200)

        response = client.get('/protected/sub1/')
        self.failUnlessEqual(response.status_code, 200)

        response = client.get('/protected/sub1/sub2/')
        self.failUnlessEqual(response.status_code, 200)


    def testForwardToken(self):

        client = Client()

        # test forwarding of token
        url = '/protected/'

        token = Token(url=url)
        token.save()

        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)

        response = client.get(token.forward_token_url())
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(response.context['token'].can_forward, False)
        self.failUnlessEqual(force_unicode(response.context['error']), 'Apologies! This token can not be forwarded.')

        token.delete()

        token = Token(url=url, forward_count=None)
        token.save()

        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)

        response = client.get(token.forward_token_url())
        self.failUnlessEqual(response.context['token'].can_forward, True)
        self.failUnlessEqual(force_unicode(response.context['error'], strings_only=True), None)

        response = client.post(token.forward_token_url(), FORM_DATA_FORWARD_1)
        self.failUnlessEqual(response.status_code, 302)

        token.delete()

        # test max number of forwards
        url = '/protected/'
        token = Token(url=url, forward_count=3)
        token.save()
        
        response = client.get(token.use_token_url())
        response = client.get(token.forward_token_url())
        self.failUnlessEqual(force_unicode(response.context['error'], strings_only=True), None)

        response = client.post(token.forward_token_url(), FORM_DATA_FORWARD_1)
        self.failUnlessEqual(response.status_code, 302)

        # grab token from db
        token = Token.objects.get(pk=token.pk)

        self.failUnlessEqual(token.forward_count, 1)

        response = client.post(token.forward_token_url(), FORM_DATA_FORWARD_1)
        self.failUnlessEqual(response.status_code, 200)

        # grab token from db
        token = Token.objects.get(pk=token.pk)
        self.failUnlessEqual(token.forward_count, 1)

        response = client.post(token.forward_token_url(), FORM_DATA_FORWARD_2)
        self.failUnlessEqual(response.status_code, 302)

        # grab token from db
        token = Token.objects.get(pk=token.pk)
        self.failUnlessEqual(token.forward_count, 0)


    def testTokenAuthLogin(self):

        client = Client()

        settings.MIDDLEWARE_CLASSES = list(settings.MIDDLEWARE_CLASSES) + ['token_auth.middleware.TokenAuthLoginMiddleware']

        from django.contrib.auth.models import User
        user = User.objects.get(pk=1)

        url = '/protected/'
        token = Token(url=url, email=user.email)
        token.save()

        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)

        response = client.get('/protected/')
        self.failUnlessEqual(response.status_code, 200)

        token.delete()

        response = client.get('/protected/')
        self.failUnlessEqual(response.status_code, 200)
