from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from model import Secret
import latitude
import oauth
import oauth_appengine
import urllib

LATITUDE_OAUTH_START_PATH = '/latitude_oauth_start'
LATITUDE_OAUTH_CALLBACK_PATH = '/latitude_oauth_callback'

def make_url(request, path, *args):
    return (request.host_url + path) % args

oauth_consumer = oauth.OAuthConsumer(
    Secret.get('oauth_consumer_key'), Secret.get('oauth_consumer_secret'))


def redirect_to_authorization_url(
    handler, oauth_client, callback_url, parameters):
    """Sends the user to an OAuth authorization page."""
    # Get a request token.
    helper = oauth_appengine.OAuthDanceHelper(oauth_client)
    request_token = helper.RequestRequestToken(callback_url, parameters)

    # Save the request token in cookies so we can pick it up later.
    handler.response.headers.add_header(
        'Set-Cookie', 'request_key=' + request_token.key)
    handler.response.headers.add_header(
        'Set-Cookie', 'request_secret=' + request_token.secret)

    # Send the user to the authorization page.
    handler.redirect(
        helper.GetAuthorizationRedirectUrl(request_token, parameters))

def handle_authorization_finished(handler, oauth_client):
    """Handles a callback from the OAuth authorization page and returns
    a freshly minted access token."""
    # Pick up the request token from the cookies.
    request_token = oauth.OAuthToken(
        handler.request.cookies['request_key'],
        handler.request.cookies['request_secret'])

    # Upgrade our request token to an access token, using the verifier.
    helper = oauth_appengine.OAuthDanceHelper(oauth_client)
    access_token = helper.RequestAccessToken(
        request_token, handler.request.get('oauth_verifier', None))

    # Clear the cookies that contained the request token.
    handler.response.headers.add_header('Set-Cookie', 'request_key=')
    handler.response.headers.add_header('Set-Cookie', 'request_secret=')

    return access_token


class LatitudeOauthStartHandler(webapp.RequestHandler):
    def get(self):
        parameters = {
            'scope': latitude.LatitudeOAuthClient.SCOPE,
            'domain': Secret.get('oauth_consumer_key'),
            'granularity': 'best',
            'location': 'all'
        }
        redirect_to_authorization_url(
            self, latitude.LatitudeOAuthClient(oauth_consumer),
            make_url(self.request, LATITUDE_OAUTH_CALLBACK_PATH), parameters)


class LatitudeOauthCallbackHandler(webapp.RequestHandler):
    def get(self):
        access_token = handle_authorization_finished(
            self, latitude.LatitudeOAuthClient(oauth_consumer))

        # Request the user's location
        client = latitude.LatitudeOAuthClient(oauth_consumer, access_token)
        result = latitude.Latitude(client).get_current_location()
        self.response.out.write(result.content)


class Main(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello.')


if __name__ == '__main__':
    run_wsgi_app(webapp.WSGIApplication([
        ('/', Main),
        (LATITUDE_OAUTH_START_PATH, LatitudeOauthStartHandler),
        (LATITUDE_OAUTH_CALLBACK_PATH, LatitudeOauthCallbackHandler)
    ]))
