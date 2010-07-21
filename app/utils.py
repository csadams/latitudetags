# Copyright 2010 Google
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

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
import cgitb
import crypto
import google.appengine.ext.webapp.template
import google.appengine.ext.webapp.util
import logging
import model
import os
import re
import sys
import urllib

ROOT = os.path.dirname(__file__)


class ErrorMessage(Exception):
    """Raise this exception to show an error message to the user."""
    def __init__(self, status, message):
        self.status = status
        self.message = message


class Redirect(Exception):
    """Raise this exception to redirect to another page."""
    def __init__(self, url):
        self.url = url


class Handler(webapp.RequestHandler):
    def render(self, path, **params):
        """Renders the template at the given path with the given parameters."""
        self.write(webapp.template.render(os.path.join(ROOT, path), params))

    def write(self, text):
        """Writes the body of the HTTP reply."""
        self.response.out.write(text)

    def initialize(self, request, response):
        """Sets up useful handler variables for every request."""
        webapp.RequestHandler.initialize(self, request, response)
        self.user = users.get_current_user()
        if self.user:
            self.xsrf_key = model.Config.get_or_generate('xsrf_key')

    def set_signature(self, lifetime=None):
        """Generates a signature to prevent XSRF (a confused deputy attack)."""
        self.user.signature = crypto.sign(
            self.xsrf_key, self.user.user_id(), lifetime)

    def verify_signature(self):
        """Verify that the incoming request includes a valid signature."""
        if not crypto.verify(
            self.xsrf_key, self.user.user_id(), self.request.get('signature')):
            raise ErrorMessage(400, 'Invalid signature.')

    def require_user(self):
        """Ensures that the user is logged in."""
        if not self.user:
            raise Redirect(users.create_login_url(self.request.uri))

    def require_member(self):
        """Ensures that the user has registered and authorized this app."""
        self.member = model.Member.get(users.get_current_user())
        if not self.member:
            raise Redirect('/_register?' + urlencode(next=self.request.uri))

    def handle_exception(self, exception, debug_mode):
        """Adds special exception handling for Redirect and ErrorMessage."""
        if isinstance(exception, Redirect):  # redirection
            self.redirect(exception.url)
        elif isinstance(exception, ErrorMessage):  # user-facing error message
            self.error(exception.status)
            self.response.clear()
            self.render('templates/error.html', message=exception.message)
        else:
            self.error(500)
            logging.exception(exception)
            if debug_mode:
                self.response.clear()
                self.write(cgitb.html(sys.exc_info()))


def clean_tag(tag):
    """Normalizes a tag string."""
    return re.sub('[^A-Za-z0-9]', '', tag).lower()


def run(*args, **kwargs):
    webapp.util.run_wsgi_app(webapp.WSGIApplication(*args, **kwargs))


def urlencode(*args, **kwargs):
    return urllib.urlencode(kwargs)
