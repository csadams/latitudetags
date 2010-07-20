import latitude
import utils

def latitudeClient(service):
    access_token = oauth_appengine.OAuthToken.toRealOAuthToken(
        service.access_token)

  # Construct client
    oauth_client = latitude.LatitudeOAuthClient(
        oauth_consumer=oauth.OAuthConsumer(GOOGLE_CONSUMER_KEY,
            GOOGLE_CONSUMER_SECRET),
        oauth_token=access_token)
    return latitude.Latitude(oauth_client)

class Join(utils.Handler):
    def get(self):
        self.write('''
<p>
<form>
Join <input name="tag" value="#">
for <select name="duration">
<option value="600">10 minutes</option>
<option value="3600">1 hour</option>
<option value="7200">2 hours</option>
<option value="21600">6 hours</option>
<option value="86400">24 hours</option>
<option value="172800">48 hours</option>
</select>.
<p>
<input type="submit"
value="Join this group and share my location with everyone in it">
</form>
        ''')

if __name__ == '__main__':
    utils.run([('/join', Join)])
