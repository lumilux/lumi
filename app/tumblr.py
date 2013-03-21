# cleaned up from https://gist.github.com/codingjester/1389963

import base64
import hashlib
import hmac
import httplib
import json
import sys
import time
import urllib
import urlparse


class TumblrAPI:
    def __init__(self, cred):
        self.consumer_key = cred.app_key
        self.secret_key = cred.app_secret
        self.oauth_token = cred.oauth_token
        self.oauth_token_secret = cred.oauth_token_secret

    def _parse(self, url):
        p = urlparse.urlparse(url)
        return p.netloc, p.netloc, p.path

    def oauth_sig(self, method, uri, params):
        """
        Creates the valid OAuth signature.
        """
        # e.g. POST&http%3A%2F%2Fapi.tumblr.com%2Fv2%2Fblog%2Fexample.tumblr.com%2Fpost
        encoded_uri = urllib.quote(uri).replace('/', '%2F')

        # escapes all the key parameters, we then strip and url encode these guys
        def encode_key(k):
            return urllib.quote(k) +'%3D'+ urllib.quote(params[k]).replace('/', '%2F')
        encoded_params = '%26'.join(encode_key(k) for k in sorted(params.keys()))

        s = method + '&' + encoded_uri + '&' + encoded_params
        s = s.replace('%257E', '~')
        secrets = self.secret_key + '&' + self.oauth_token_secret
        return urllib.quote(base64.encodestring(hmac.new(secrets, s, hashlib.sha1).digest()).strip())

    def _oauth_gen(self, method, url, iparams, headers):
        """
        Creates the oauth parameters we're going to need to sign the body
        """
        def encode_value(v):
            return urllib.quote(str(v)).replace('/', '%2F')
        params = dict([(k, encode_value(v)) for k, v in iparams.iteritems()])
        params['oauth_consumer_key'] = self.consumer_key
        params['oauth_nonce'] = str(time.time())[::-1]
        params['oauth_signature_method'] = 'HMAC-SHA1'
        params['oauth_timestamp'] = str(int(time.time()))
        params['oauth_version'] = '1.0'
        params['oauth_token']= self.oauth_token
        params['oauth_signature'] = self.oauth_sig(method, 'http://' + headers['Host'] + url, params)
        oauth_params = ',  '.join('{0}="{1}"'.format(k, v) for k, v in params.iteritems() if 'oauth' in k)
        headers['Authorization' ] =  'OAuth ' + oauth_params

    def _post_oauth(self, url, params=None):
        """
        Does the actual posting. Content-type is set as x-www-form-urlencoded
        Everything url-encoded and data is sent through the body of the request.
        """
        if not params:
            params = {}

        machine, host, uri = self._parse(url)
        headers = {'Host': host, 'Content-type': 'application/x-www-form-urlencoded'}
        self._oauth_gen('POST', uri, params, headers)
        conn = httplib.HTTPConnection(machine)

        # urlencode the parameters and make sure to kill any trailing slashes
        encoded_params = urllib.urlencode(params).replace('/', '%2F')
        conn.request('POST', uri, encoded_params, headers)
        return conn.getresponse()

    def _resp(self, resp, code=200):
        if resp.status != code:
            raise Exception('response code is {0} - {1}'.format(resp.status, resp.read()))
        return json.loads(resp.read())['response']

    def post(self, id, params=None):
        if not params:
            params = {}
        url = 'http://api.tumblr.com/v2/blog/{0}/post'.format(id)
        return self._resp(self._post_oauth(url, params), 201);

