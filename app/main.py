# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A simple app that performs the OAuth dance and makes a Latitude request."""

__author__ = 'Ka-Ping Yee <kpy@google.com>'


from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
import latitude
import oauth
import oauth_webapp

# Go to the LATITUDE_OAUTH_START_PATH to start the OAuth dance.
LATITUDE_OAUTH_START_PATH = '/latitude_oauth_start'
LATITUDE_OAUTH_CALLBACK_PATH = '/latitude_oauth_callback'


# To set up this application as an OAuth consumer:
# 1. Go to https://www.google.com/accounts/ManageDomains
# 2. Follow the instructions to register and verify your domain
# 3. The administration page for your domain should now show an "OAuth
#    Consumer Key" and "OAuth Consumer Secret".  Put these values into
#    the app's datastore by calling OAuthConfig.set('consumer_key', ...)
#    and OAuthConfig.set('consumer_secret', ...).

class OAuthConfig(db.Model):
    value = db.ByteStringProperty()

    @staticmethod
    def get(name):
        secret = OAuthConfig.get_by_key_name(name)
        return secret and secret.value or None

    @staticmethod
    def set(name, value):
        OAuthConfig(key_name=name, value=value).put()


oauth_consumer = oauth.OAuthConsumer(
    OAuthConfig.get('consumer_key'), OAuthConfig.get('consumer_secret'))


class LatitudeOAuthStartHandler(webapp.RequestHandler):
    def get(self):
        parameters = {
            'scope': latitude.LatitudeOAuthClient.SCOPE,
            'domain': OAuthConfig.get('consumer_key'),
            'granularity': 'best',
            'location': 'all'
        }
        oauth_webapp.redirect_to_authorization_page(
            self, latitude.LatitudeOAuthClient(oauth_consumer),
            self.request.host_url + LATITUDE_OAUTH_CALLBACK_PATH, parameters)


class LatitudeOAuthCallbackHandler(webapp.RequestHandler):
    def get(self):
        access_token = oauth_webapp.handle_authorization_finished(
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
        (LATITUDE_OAUTH_START_PATH, LatitudeOAuthStartHandler),
        (LATITUDE_OAUTH_CALLBACK_PATH, LatitudeOAuthCallbackHandler)
    ]))
