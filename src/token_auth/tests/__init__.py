from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.contrib.auth.models import User
from token_auth.models import ProtectedURL, TokenURL, ProtectedURLToken
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
import datetime
 
emails = 'test@test.com;test2@test.com'
 
form_data_url_1 = { 'url': '/protected/', 'valid_until': '', 'emails': emails }
form_data_url_2 = { 'url': '/protected/sub1/', 'valid_until': '', 'emails': emails }
form_data_url_3 = { 'url': '/protected/sub1/sub2/', 'valid_until': '', 'emails': emails }
 
form_data_forward = { 'emails': emails }
form_data_forward_1 = { 'emails': 'test@test.com' }
 
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
 
        response = client.get(reverse('protectedurl_create'))
        self.failUnlessEqual(response.status_code, 302)
        
        self.login(client)
        
        response = client.get(reverse('protectedurl_create'))
 
        self.failUnlessEqual(response.status_code, 200)
        self.failUnless(response, "no form in context")
        self.failUnlessEqual(response.context['form'].errors, {})
        
        response = client.post(reverse('protectedurl_create'), form_data_url_1)
        self.failUnlessEqual(response.status_code, 302)
        
        response = client.post(reverse('protectedurl_create'), form_data_url_2)
        self.failUnlessEqual(response.status_code, 302)
        
        response = client.post(reverse('protectedurl_create'), form_data_url_3)
        self.failUnlessEqual(response.status_code, 302)
        
    def testVisitURL302(self):
        
        client = Client()
        
        response = client.get('/protected/')
        self.failUnlessEqual(response.status_code, 302)
        
        response = client.get('/protected/sub1/')
        self.failUnlessEqual(response.status_code, 302)
        
        response = client.get('/protected/sub1/sub2/')
        self.failUnlessEqual(response.status_code, 302)
 
    def testVisitURL200Cookie(self):
        
        url, created = TokenURL.objects.get_or_create(url='/protected/')
        
        token = ProtectedURLToken(url=url)
        token.save()
        
        client = Client()
        
        # test that protection works
        response = client.get("/protected/")
        self.failUnlessEqual(response.status_code, 302)
        
        response = client.get("/protected/sub1/")
        self.failUnlessEqual(response.status_code, 302)
        
        response = client.get("/protected/sub1/sub2/")
        self.failUnlessEqual(response.status_code, 302)
        
        # test that tokens work
        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)
        self.failUnlessEqual(client.cookies["protectedurltokens"].value, token.token)
 
        response = client.get("/protected/")
        self.failUnlessEqual(response.status_code, 200)
        
        response = client.get("/protected/sub1/")
        self.failUnlessEqual(response.status_code, 200)
        
        response = client.get("/protected/sub1/sub2/")
        self.failUnlessEqual(response.status_code, 200)
        
        settings.PROTECTEDURL_GENERATE_COOKIE_ONCE = False
        
        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)
                
        settings.PROTECTEDURL_GENERATE_COOKIE_ONCE = True
 
        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.context['token_used'], True)
        
        # test for two tokens
        token2 = ProtectedURLToken(url=url)
        token2.save()
 
        response = client.get(token2.use_token_url())
        self.failUnlessEqual(response.status_code, 302)
        self.failUnless(client.cookies["protectedurltokens"].value, token.token + '|' + token2.token)
        
        token.delete()
        token2.delete()
        
        # test for expired tokens
        token3 = ProtectedURLToken(url=url)
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
        url, created = TokenURL.objects.get_or_create(url='/protected/')
        
        token = ProtectedURLToken(url=url)
        token.save()
 
        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)
 
        response = client.get(token.forward_token_url())
        self.failUnlessEqual(response.context['token'].can_forward, False)
        self.failUnlessEqual(force_unicode(response.context['error']), 'Apologies! You are not allowed to forward this token.')
        
        token.delete()
        
        token = ProtectedURLToken(url=url, forward_count=None)
        token.save()
        
        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)
        
        response = client.get(token.forward_token_url())
        self.failUnlessEqual(response.context['token'].can_forward, True)
        self.failUnlessEqual(force_unicode(response.context['error'], strings_only=True), None)
        
        response = client.post(token.forward_token_url(), form_data_forward)
        self.failUnlessEqual(response.status_code, 302)
        
        token.delete()
        
        # test max number of forwards
        url, created = TokenURL.objects.get_or_create(url='/protected/')
        token = ProtectedURLToken(url=url, forward_count=3)
        token.save()
        
        response = client.get(token.forward_token_url())
        self.failUnlessEqual(response.context['error'], None)
        
        response = client.post(token.forward_token_url(), form_data_forward)
        self.failUnlessEqual(response.status_code, 302)
        
        # grab token from db
        token = ProtectedURLToken.objects.get(pk=token.pk)
        
        self.failUnlessEqual(token.forward_count, 1)
        
        response = client.post(token.forward_token_url(), form_data_forward)
        self.failUnlessEqual(response.status_code, 200)
        
        # grab token from db
        token = ProtectedURLToken.objects.get(pk=token.pk)
        self.failUnlessEqual(token.forward_count, 1)
        
        response = client.post(token.forward_token_url(), form_data_forward_1)
        self.failUnlessEqual(response.status_code, 302)
        
        # grab token from db
        token = ProtectedURLToken.objects.get(pk=token.pk)
        self.failUnlessEqual(token.forward_count, 0)
        
    def testTokenAuthLogin(self):
        
        client = Client()
        
        settings.MIDDLEWARE_CLASSES = list(settings.MIDDLEWARE_CLASSES) + ['token_auth.middleware.TokenAuthLoginMiddleware']
        
        from django.contrib.auth.models import User
        user = User.objects.get(pk=1)
        
        url, created = TokenURL.objects.get_or_create(url='/protected/')
        token = ProtectedURLToken(url=url, email=user.email)
        token.save()
        
        response = client.get(token.use_token_url())
        self.failUnlessEqual(response.status_code, 302)
        
        response = client.get('/protected/')
        self.failUnlessEqual(response.status_code, 200)
        
        token.delete()
                
        response = client.get('/protected/')
        self.failUnlessEqual(response.status_code, 200) 