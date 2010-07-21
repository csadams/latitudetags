# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tag viewing page for the Latitude Tags application."""

__author__ = 'Ka-Ping Yee <kpy@google.com>'

from google.appengine.api.labs import taskqueue
import datetime
import model
import simplejson
import utils


class Tag(utils.Handler):
    def get(self, tag):
        # To allow a join action to redirect to OAuth and smoothly redirect
        # back here to finish the action, the join action is a GET request.
        if self.request.get('join'):
            # Add a tag to the member, and also update the member's location.
            self.require_member()
            self.verify_signature()
            now = datetime.datetime.utcnow()
            duration = int(self.request.get('duration'))
            stop_time = now + datetime.timedelta(0, duration)
            self.member.set_location(utils.get_location(self.member), now)
            model.Member.join(self.user, tag, stop_time)
            # Schedule a task to promptly update the stats upon expiry.
            taskqueue.add(countdown=duration + 1, method='GET',
                          url='/_update_tagstats', params={'tag': tag})
            # Redirect to avoid adding the join action to the browser history.
            raise utils.Redirect('/' + tag)

        if self.request.get('quit'):
            # Remove membership to this tag.
            self.require_member()
            self.verify_signature()
            model.Member.quit(self.user, tag)
            # Redirect to avoid adding the join action to the browser history.
            raise utils.Redirect('/' + tag)

        if self.request.get('quit_all'):
            # Remove the user's registration and Latitude API authorization.
            self.require_member()
            self.verify_signature()
            self.member.delete()
            raise utils.Redirect('/')

        # Generate the tag viewing page.
        now = datetime.datetime.utcnow()
        members_json = []
        for member in model.Member.get_for_tag(tag, now):
            member_json = {'nickname': member.nickname,
                           'lat': member.location.lat,
                           'lon': member.location.lon}
            if self.user and self.user.user_id() == member.user.user_id():
                member_json['self'] = 1
            members_json.append(member_json)

        if self.user:
            self.set_signature()  # to prevent XSRF
        self.render('templates/tag.html', tag=tag,
                    user=self.user, member=model.Member.get(self.user),
                    members_json=simplejson.dumps(members_json))


if __name__ == '__main__':
    utils.run([('/(.*)', Tag)], debug=True)
