#!/usr/bin/env python
#
# Copyright 2009 Joe LaPenna
# Copyright 2009 Google

"""
An appengine OAuthClient based on the oauth-python reference implementation.
"""

import logging

import oauth

from google.appengine.api import urlfetch
from google.appengine.ext import db


class OAuthConsumer(db.Model):
    """Consumer of OAuth authentication.

    OAuthConsumer is a data type that represents the identity of the Consumer
    via its shared secret with the Service Provider.

    Includes classmethods to convert to the reference implementation class of
    the same name.
    """

    key_ = db.StringProperty(name='key')
    secret = db.StringProperty()

    @classmethod
    def fromOAuthConsumer(consumer):
        """Transform an oauth.OAuthConsumer instance to an OAuthConsumer.

        This does not put() the instance.
        """
        return OAuthConsumer(
            key=consumer.key,
            secret=consumer.secret)

    @classmethod
    def toOAuthConsumer(consumer):
        """Transform a OAuthConsumer instance to an oauth.OAuthConsumer."""
        new_consumer = oauth.OAuthConsumer(consumer.key, consumer.secret)
        new_consumer._key = consumer.key()    # For debugging.
        return new_consumer


class OAuthToken(db.Model):
    """A data type that represents an End User via either an access
    or request token.

    key -- the token
    secret -- the token secret

    Includes classmethods to convert to the reference implemenation class of
    the same name.
    """

    token_key = db.StringProperty()
    secret = db.StringProperty()
    callback = db.StringProperty()
    callback_confirmed = db.BooleanProperty()
    verifier = db.StringProperty()

    @classmethod
    def fromOAuthToken(cls, token):
        """Transform an oauth.OAuthToken instance to an OAuthToken.

        This does not put() the instance.
        """
        return OAuthToken(
            token_key=token.key,
            secret=token.secret,
            callback=token.callback,
            # Ugh, no likely with google oauth.
            #callback_confirmed=token.callback_confirmed,
            verifier=token.verifier)

    @classmethod
    def toRealOAuthToken(cls, entity):
        """Transform a OAuthToken instance to an oauth.OAuthToken."""
        new_token = oauth.OAuthToken(entity.token_key, entity.secret)
        new_token.callback = entity.callback
        new_token.callback_confirmed = entity.callback_confirmed
        new_token.verifier = entity.verifier
        return new_token


class OAuthClient(oauth.OAuthClient):
    """A worker to attempt to execute a request (on appengine)."""

    def __init__(self, oauth_consumer, oauth_token, request_token_url='',
                 access_token_url='', authorization_url=''):
        super(OAuthClient, self).__init__(oauth_consumer, oauth_token)
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url

    def fetch_request_token(self, oauth_request):
        """-> OAuthToken."""
        # Using headers or payload varies by service...
        response = urlfetch.fetch(
            url=self.request_token_url,
            method=oauth_request.http_method,
            #headers=oauth_request.to_header(),
            payload=oauth_request.to_postdata())
        logging.info(response.content)
        return oauth.OAuthToken.from_string(response.content)

    def fetch_access_token(self, oauth_request):
        """-> OAuthToken."""
        response = urlfetch.fetch(
            url=self.access_token_url,
            method=oauth_request.http_method,
            headers=oauth_request.to_header())
        logging.info(response.content)
        return oauth.OAuthToken.from_string(response.content)

    def access_resource(self, oauth_request, deadline=None):
        """-> Some protected resource."""
        if oauth_request.http_method == 'GET':
            url = oauth_request.to_url()
            logging.info(url)
            logging.info(oauth_request.to_header())
            return urlfetch.fetch(
                url=url,
                method=oauth_request.http_method)
        else:
            payload = oauth_request.to_postdata()
            return urlfetch.fetch(
                url=oauth_request.get_normalized_http_url(),
                method=oauth_request.http_method,
                payload=payload)
                #, headers=oauth_request.to_header())


class OAuthDanceHelper(object):

    def __init__(self, oauth_client):
        self.oauth_client = oauth_client

    def RequestRequestToken(self, callback, parameters=None):
        """Request a request token."""
        import logging
        logging.info('RequestRequestToken %r' % [callback, parameters])
        request_token_request = oauth.OAuthRequest.from_consumer_and_token(
            self.oauth_client.get_consumer(),
            token=None,
            callback=callback,
            http_method='POST',
            http_url=self.oauth_client.request_token_url,
            parameters=parameters)

        # Request a token that we can use to redirect the user to an auth url.
        request_token_request.sign_request(
            self.oauth_client.signature_method,
            self.oauth_client.get_consumer(),
            None)
        return self.oauth_client.fetch_request_token(request_token_request)

    def GetAuthorizationRedirectUrl(self, request_token, parameters=None):
        """A url to redirect a user's browser to."""
        authorization_request = oauth.OAuthRequest.from_token_and_callback(
            request_token,
            http_method='GET',    # Before 5/21/2010 it was POST...
            http_url=self.oauth_client.authorization_url,
            parameters=parameters)
        return authorization_request.to_url()

    def RequestAccessToken(self, request_token, verifier=None):
        """Request an access (get resources with this) token."""
        access_request = oauth.OAuthRequest.from_consumer_and_token(
            self.oauth_client.get_consumer(),
            token=request_token,
            verifier=verifier,
            http_url=self.oauth_client.access_token_url)

        access_request.sign_request(
            self.oauth_client.signature_method,
            self.oauth_client.get_consumer(),
            request_token)
        return self.oauth_client.fetch_access_token(access_request)
