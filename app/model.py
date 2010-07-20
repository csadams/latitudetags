# Copyright 2009-2010 by Ka-Ping Yee
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

class Secret(db.Model):
    value = db.ByteStringProperty()

    @staticmethod
    def get(name):
        secret = Secret.get_by_key_name(name)
        return secret and secret.value or None

    @staticmethod
    def set(name, value):
        Secret(key_name=name, value=value).put()

    @staticmethod
    def get_or_generate(name):
        random_key = ''.join('%02x' % random.randrange(256) for i in range(16))
        return Secret.get_or_insert(key_name=name, value=random_key).value
