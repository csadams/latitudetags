from google.appengine.ext import webapp
from model import Secret
import latitude
import logging
import oauth
import oauth_appengine
import urllib
import utils

LATITUDE_OAUTH_START_PATH = '/latitude_oauth_start'
LATITUDE_OAUTH_CALLBACK_PATH = '/latitude_oauth_callback'
START_PATH = '/'

def make_url(request, path, *args):
    return (request.host_url + path) % args

oauth_consumer = oauth.OAuthConsumer(
    Secret.get('oauth_consumer_key'), Secret.get('oauth_consumer_secret'))

class OAuthStartHandler(webapp.RequestHandler):
    """Starts the OAuth process.

    Gets a temporary token and redirects to the service's login handler.
    """

    def initialize(self, request, response):
        super(OAuthStartHandler, self).initialize(request, response)
        self.service_name = None
        self.oauth_client = None
        self.callback_path = None
        self.parameters = {}

    def get(self, user=None, session=None):
        # Get a request token.
        helper = oauth_appengine.OAuthDanceHelper(self.oauth_client)
        request_token = helper.RequestRequestToken(
            make_url(self.request, self.callback_path),
            parameters=self.parameters)
        logging.info('got request token %r' % request_token)

        # Put the request token in a cookie so we can pick it up later.
        self.response.headers.add_header(
            'Set-Cookie', 'request_key=' + request_token.key)
        self.response.headers.add_header(
            'Set-Cookie', 'request_secret=' + request_token.secret)

        # Send the user to the authorization page.
        url = helper.GetAuthorizationRedirectUrl(request_token, self.parameters)
        logging.info('Redirect: %s' % url)
        self.redirect(url)


class OAuthCallbackHandler(webapp.RequestHandler):
    """After the user logs into the target service, they're redirected here.

    On successful lookup, will store the user's auth token in their session.
    """

    def initialize(self, request, response):
        super(OAuthCallbackHandler, self).initialize(request, response)
        self.service_name = None
        self.oauth_client = None
        self.redirect_path = None

    def get(self):
        logging.info('Cookies: %r' % self.request.cookies)
        request_token = oauth.OAuthToken(
            self.request.cookies['request_key'],
            self.request.cookies['request_secret'])
        logging.info('key: %s' % str(request_token.key))
        logging.info('secret: %s' % str(request_token.secret))

        # Find the key from the request
        key_name = self.request.get('oauth_token', None)
        verifier = self.request.get('oauth_verifier', None)

        # Request a token that we can use to access resources.
        helper = oauth_appengine.OAuthDanceHelper(self.oauth_client)
        access_token = helper.RequestAccessToken(
            request_token, verifier=verifier)

        logging.info('key: %s' % str(access_token.key))
        logging.info('secret: %s' % str(access_token.secret))

        # Save it for later
        oauth_access_token = \
            oauth_appengine.OAuthToken.fromOAuthToken(access_token)

        # Request the user's location
        client = latitude.LatitudeOAuthClient(
            oauth_consumer, access_token)
        lat = latitude.Latitude(client)
        result = lat.get_current_location()
        logging.info('result: %r' % result)
        logging.info('result: %r' % result.status_code)
        logging.info('result: %r' % result.content)
        self.response.out.write(result.content)

        # Redirect user
        url = make_url(self.request, self.redirect_path)
        logging.info('Redirect: %s' % url)
        #self.redirect(url)


class LatitudeOAuthStartHandler(OAuthStartHandler):
    """Starts the oAuth process for latitude."""

    def initialize(self, request, response):
        super(LatitudeOAuthStartHandler, self).initialize(request, response)
        self.service_name = 'latitude'
        self.oauth_client = latitude.LatitudeOAuthClient(oauth_consumer)
        self.callback_path = LATITUDE_OAUTH_CALLBACK_PATH
        self.parameters = {'scope': latitude.LatitudeOAuthClient.SCOPE,
                           'domain': Secret.get('oauth_consumer_key'),
                           'granularity': 'best',
                           'location': 'all'}


class LatitudeOAuthCallbackHandler(OAuthCallbackHandler):
    """After the user logs into latitude, they're redirected here."""

    def initialize(self, request, response):
        super(LatitudeOAuthCallbackHandler, self).initialize(request, response)
        self.service_name = 'latitude'
        self.oauth_client = latitude.LatitudeOAuthClient(oauth_consumer)
        self.redirect_path = START_PATH


class Main(utils.Handler):
    def get(self):
        self.write('Hello.')


if __name__ == '__main__':
    utils.run([('/', Main),
               (LATITUDE_OAUTH_START_PATH, LatitudeOAuthStartHandler),
               (LATITUDE_OAUTH_CALLBACK_PATH, LatitudeOAuthCallbackHandler)])
