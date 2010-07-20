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

from google.appengine.ext import db
import datetime


class Member(db.Model):
    """Represents a user who has authorized hashlatitude.
    key_name: user.user_id()"""
    user = db.UserProperty()
    latitude_key = db.ByteStringProperty()  # OAuth access token key
    latitude_secret = db.ByteStringProperty()  # OAuth access token secret
    location = db.GeoPtProperty()  # user's geolocation
    location_time = db.DateTimeProperty()  # time that location was recorded
    tags = db.StringListProperty()  # list of groups this user has joined
    stop_times = db.ListProperty(datetime.datetime)  # membership ending times

    # tags and stop_times are parallel arrays!
    # INVARIANT: len(tags) == len(stop_times)

    def remove_tag(self, tag):
        """Removes a tag from self.tags, preserving the invariant."""
        if tag in self.tags:
            index = self.tags.index(tag)
            self.tags[index:index + 1] = []
            self.stop_times[index:index + 1] = []

    @staticmethod
    def create(user):
        return Member(key_name=user.user_id(), user=user)

    @staticmethod
    def get(user):
        if user:
            return Member.get_by_key_name(user.user_id())

    @staticmethod
    def join(user, tag, stop_time):
        def work():
            member = Member.get(user)
            member.remove_tag(tag)
            member.tags.append(tag)
            member.stop_times.append(stop_time)
            member.put()
        db.run_in_transaction(work)

    @staticmethod
    def leave(user, tag):
        def work():
            member = Member.get(user)
            member.remove_tag(tag)
            member.put()
        db.run_in_transaction(work)

    @staticmethod
    def clean(key, now):
        def work():
            member = db.get(key)
            index = 0
            while index < len(member.tags):
                if member.stop_times[index] <= now:
                    member.remove_tag(member.tags[index])
                else:
                    index += 1
            member.put()
        db.run_in_transaction(work)


class Group(db.Model):
    """Represents stale statistics about a particular group.
    key_name: tag"""
    update_time = db.DateTimeProperty(auto_now=True)
    member_count = db.IntegerProperty()
    centroid = db.GeoPtProperty()  # centroid of member locations
    radius = db.FloatProperty()  # RMS member distance from centroid
