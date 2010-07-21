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

import datetime
import model
import time
import utils


class Tag(utils.Handler):
    def get(self, tag):
        # To allow a join action to redirect to OAuth and smoothly redirect
        # back here to finish the action, the join action is a GET request.
        if self.request.get('join'):
            self.require_member()
            self.verify_signature()
            duration = int(self.request.get('duration'))
            stop_time = datetime.datetime.utcfromtimestamp(
                time.time() + duration)
            model.Member.join(self.user, tag, stop_time)
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
        members = model.Member.all().filter('tags =', tag)
        rows = []
        for member in members:
            tag_index = member.tags.index(tag)
            stop_time = member.stop_times[tag_index]
            if stop_time > now:
                rows.append({'nickname': member.nickname,
                             'latitude': member.location.lat,
                             'longitude': member.location.lon})

        if self.user:
            self.set_signature()  # to prevent XSRF
        self.render('templates/tag.html', tag=tag, rows=rows, user=self.user)


if __name__ == '__main__':
    utils.run([('/(.*)', Tag)], debug=True)
