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

"""Datastore model definitions."""

__author__ = 'Ka-Ping Yee <kpy@google.com>'

from google.appengine.ext import db
import datetime
import random


class Config(db.Model):
    """Stores a configuration setting."""
    value = db.StringProperty()

    @staticmethod
    def get(name):
        config = Config.get_by_key_name(name)
        return config and config.value or None

    @staticmethod
    def set(name, value):
        Config(key_name=name, value=value).put()

    @staticmethod
    def get_or_generate(name):
        """Generates a random value if the setting does not already exist.
        Use this to initialize secret keys."""
        # TODO(kpy): Use memcache to avoid expensive random number generation.
        value = ''.join('%02x' % random.randrange(256) for i in range(32))
        return Config.get_or_insert(key_name=name, value=value).value


class Member(db.Model):
    """Represents a user who has registered and authorized this app.
    key_name: user.user_id()"""
    user = db.UserProperty()
    nickname = db.StringProperty()  # nickname to show with the user's location
    tags = db.StringListProperty()  # list of groups this user has joined
    stop_times = db.ListProperty(datetime.datetime)  # membership ending times
    latitude_key = db.StringProperty()  # OAuth access token key
    latitude_secret = db.StringProperty()  # OAuth access token secret
    location = db.GeoPtProperty()  # user's geolocation
    location_time = db.DateTimeProperty()  # time that location was recorded

    # NOTE: tags and stop_times are parallel arrays!
    # INVARIANT: len(tags) == len(stop_times)

    def remove_tag(self, tag):
        """Removes a tag from self.tags, preserving the invariant."""
        if tag in self.tags:
            index = self.tags.index(tag)
            self.tags[index:index + 1] = []
            self.stop_times[index:index + 1] = []

    @staticmethod
    def create(user):
        """Creates a Member object for a user."""
        return Member(key_name=user.user_id(), user=user)

    @staticmethod
    def get(user):
        """Gets the Member object for a user."""
        if user:
            return Member.get_by_key_name(user.user_id())

    @staticmethod
    def join(user, tag, stop_time):
        """Transactionally adds a tag for a user."""
        def member_work():
            member = Member.get(user)
            member.remove_tag(tag)
            member.tags.append(tag)
            member.stop_times.append(stop_time)
            member.put()

        def tagstat_work():
            tagstat = TagStat.get(tag) or TagStat(key_name=tag, member_count=0)
            tagstat.member_count += 1
            tagstat.put()

        db.run_in_transaction(member_work)
        db.run_in_transaction(tagstat_work)

    @staticmethod
    def quit(user, tag):
        """Transactionally removes a tag for a user."""
        def member_work():
            member = Member.get(user)
            member.remove_tag(tag)
            member.put()

        def tagstat_work():
            tagstat = TagStat.get(tag) or TagStat(key_name=tag, member_count=1)
            tagstat.member_count -= 1
            tagstat.put()

        db.run_in_transaction(member_work)
        db.run_in_transaction(tagstat_work)

    def clean(self, now):
        """Transactionally removes all expired tags for this member."""
        def work():
            member = db.get(self.key())
            index = 0
            while index < len(member.tags):
                if member.stop_times[index] <= now:
                    # We don't bother to update member_count here;
                    # update_tagstats will eventually take care of it.
                    member.remove_tag(member.tags[index])
                else:
                    index += 1
            member.put()
            return member
        # Test if cleaning is needed, before starting a transaction.
        if self.stop_times and min(self.stop_times) <= now:
            return db.run_in_transaction(work)
        return self

    def set_location(self, location, now):
        """Transactionally sets the location for this member."""
        def work():
            member = db.get(self.key())
            member.location = location
            member.location_time = now
            member.put()
        db.run_in_transaction(work)


class TagStat(db.Model):
    """Contains periodically updated statistics about a particular tag.
    key_name: tag"""
    update_time = db.DateTimeProperty(auto_now=True)
    member_count = db.IntegerProperty(default=0)
    centroid = db.GeoPtProperty()  # centroid of member locations
    radius = db.FloatProperty()  # RMS member distance from centroid

    @staticmethod
    def get(tag):
        return TagStat.get_by_key_name(tag)
