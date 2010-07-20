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
import utils


class View(utils.Handler):
    def get(self, tag):
        now = datetime.datetime.utcnow()
        members = model.Member.all().filter('tags =', tag)
        rows = []
        for member in members:
            tag_index = member.tags.index(tag)
            stop_time = member.stop_times[tag_index]
            if stop_time > now:
                rows.append({'name': member.user.nickname(),
                             'latitude': member.location.lat,
                             'longitude': member.location.lon})
        self.render('templates/view.html', tag=tag, rows=rows)


if __name__ == '__main__':
    utils.run([('/view/(.*)', View)])
