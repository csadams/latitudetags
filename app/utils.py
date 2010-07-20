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
import google.appengine.ext.webapp.template
import google.appengine.ext.webapp.util
import logging
import model
import os

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
        self.response.out.write(text)

    def require_user(self):
        """Ensures that the user is logged in."""
        user = users.get_current_user()
        if not user:
            raise Redirect(users.create_login_url(self.request.uri))
        return user

    def require_member(self):
        """Ensures that the user has authorized this app for Latitude."""
        member = model.Member.get(users.get_current_user())
        if not member:
            raise Redirect('/latitude_oauth_start')
        return member

    def handle_exception(self, exception, debug_mode):
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


def run(*args, **kwargs):
    webapp.util.run_wsgi_app(webapp.WSGIApplication(*args, **kwargs))
