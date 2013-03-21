import datetime
import json
import os
import re
import tempfile
import time

import web
from web import form
from web.contrib.template import render_jinja
from tumblpy import Tumblpy
from mongoengine import connect

from keys import *
from models import User, Photo, Post
import publish as publish_utils

TEMP_DIR = os.path.realpath(os.path.abspath(os.path.join(os.path.dirname(__file__), '../img/temp')))

connect('lumi')

urls = (
    '/admin/', 'admin',
    '/admin/upload', 'upload',
    '/admin/publish', 'publish',
    '/admin/delete', 'delete',
    '/admin/tumblrauth', 'tumblrauth',
    '/admin/login', 'login',
    '/admin/logout', 'logout',
)

render = render_jinja(
    '/usr/share/nginx/lumi/app/templates/admin',
    encoding='utf-8'
)

app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore(tempfile.mkdtemp()))

def j(obj):
    web.header('Content-Type', 'application/json')
    return json.dumps(obj)

def authenticate(func):
    def wrapped(*args, **kwargs):
        c_username = web.cookies().get('username')
        c_auth = web.cookies().get('auth')
        if not c_username or not c_auth:
            raise web.SeeOther('/admin/login')
        user = User.objects(username=c_username)[0]
        if not user.authenticate(auth=c_auth):
            raise web.SeeOther('/admin/login')
        return func(*args, **kwargs)
    return wrapped

class admin:
    @authenticate
    def GET(self):
        return render.index()

class upload:
    @authenticate
    def POST(self):
        f = web.input(file={})['file']
        #TODO: avoid using an existing filename
        filename = f.filename
        temp_path = os.path.join(TEMP_DIR, filename)
        with open(temp_path, 'wb') as t:
            t.write(f.value)
        photo = publish_utils.create_photo(temp_path)
        return j({'success': True, 'id': str(photo.id)})

class publish:
    @authenticate
    def POST(self):
        data = json.loads(web.data())
        photos = list(Photo.objects(id__in=data['photos']))
        tags = [t.strip() for t in data['tags'].split(',')] if data.get('tags') else None

        post = publish_utils.create_post(title=data['title'], photos=photos, tags=tags)
        publish_utils.emit(post)
        publish_utils.generate()

        tumblr = Tumblpy(app_key=KEYS['tumblr']['key'],
                         app_secret=KEYS['tumblr']['secret'],
                         oauth_token=KEYS['tumblr']['oauth_token'],
                         oauth_token_secret=KEYS['tumblr']['oauth_token_secret'])
        publish_utils.publish_tumblr(post, tumblr)

        return j({'success': True, 'post': post.as_dict()})

class delete:
    @authenticate
    def GET(self):
        post = publish_utils.delete_last()
        publish_utils.refresh()
        publish_utils.generate()
        return j({'success': True, 'post': post})

class tumblrauth:
    @authenticate
    def GET(self):
        data = web.input(oauth_verifier=None)
        if data.oauth_verifier:
            tumblr = Tumblpy(app_key=KEYS['tumblr']['key'],
                             app_secret=KEYS['tumblr']['secret'],
                             oauth_token=session.tumblr_oauth_token,
                             oauth_token_secret=session.tumblr_oauth_token_secret)
            auth = tumblr.get_authorized_tokens(data.oauth_verifier)
            return j({'success': True, 'auth': auth})
        else:
            tumblr = Tumblpy(app_key=KEYS['tumblr']['key'],
                             app_secret=KEYS['tumblr']['secret'],
                             callback_url='https://secure.lumilux.org/admin/tumblrauth')
            auth = tumblr.get_authentication_tokens()
            auth_url = auth['auth_url']
            session.tumblr_oauth_token = auth['oauth_token']
            session.tumblr_oauth_token_secret = auth['oauth_token_secret']
            raise web.SeeOther(auth_url)

class login:
    def GET(self):
        return render.login()

    def POST(self):
        username = web.input().username
        password = web.input().password
        if not username or not password:
            raise web.Unauthorized()
        user = User.objects(username=username)[0]
        if not user or not user.authenticate(password):
            raise web.Unauthorized()
        web.setcookie('username', user.username, 86400)
        web.setcookie('auth', user.auth, 86400)
        return j({'success': True})

class logout:
    def GET(self):
        web.setcookie('username', '', -1)
        web.setcookie('auth', '', -1)
        raise web.SeeOther('/admin/login')

    def POST(self):
        web.setcookie('username', '', -1)
        web.setcookie('auth', '', -1)
        return j({'success': True})

application = app.wsgifunc()

if __name__ == '__main__':
    print('Initialized.')
