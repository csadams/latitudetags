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

"""Request handlers for the OAuth authorization process."""

__author__ = 'Ka-Ping Yee <kpy@google.com>'


from google.appengine.ext import db
import datetime
import latitude
import model
import oauth
import oauth_webapp
import simplejson
import utils


# To set up this application as an OAuth consumer:
# 1. Go to https://www.google.com/accounts/ManageDomains
# 2. Follow the instructions to register and verify your domain
# 3. The administration page for your domain should now show an "OAuth
#    Consumer Key" and "OAuth Consumer Secret".  Put these values into
#    the app's datastore by calling Config.set('oauth_consumer_key', ...)
#    and Config.set('oauth_consumer_secret', ...).

oauth_consumer = oauth.OAuthConsumer(
    Config.get('oauth_consumer_key'), Config.get('oauth_consumer_secret'))


class LatitudeOAuthStartHandler(utils.Handler):
    def get(self):
        self.require_user()
        parameters = {
            'scope': latitude.LatitudeOAuthClient.SCOPE,
            'domain': Config.get('oauth_consumer_key'),
            'granularity': 'best',
            'location': 'all'
        }
        callback_url = self.request.host_url + utils.OAUTH_CALLBACK_PATH + \
            '?' + utils.urlencode(next=self.request.get('next', ''))
        oauth_webapp.redirect_to_authorization_page(
            self, latitude.LatitudeOAuthClient(oauth_consumer),
            callback_url, parameters)


class LatitudeOAuthCallbackHandler(utils.Handler):
    def get(self):
        user = self.require_user()
        access_token = oauth_webapp.handle_authorization_finished(
            self, latitude.LatitudeOAuthClient(oauth_consumer))

        # Request the user's location.
        client = latitude.LatitudeOAuthClient(oauth_consumer, access_token)
        result = latitude.Latitude(client).get_current_location()
        data = simplejson.loads(result.content)['data']

        # Store the new Member object.
        member = model.Member.create(user)
        member.latitude_key = access_token.key
        member.latitude_secret = access_token.secret
        member.location = db.GeoPt(data['latitude'], data['longitude'])
        member.location_time = datetime.datetime.utcnow()
        member.put()
        raise utils.Redirect(self.request.get('next', '') or '/')


if __name__ == '__main__':
    utils.run([
        (utils.OAUTH_START_PATH, LatitudeOAuthStartHandler),
        (utils.OAUTH_CALLBACK_PATH, LatitudeOAuthCallbackHandler)
    ])
