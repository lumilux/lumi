import datetime
import random
import string

import bcrypt
from mongoengine import *

SOURCES = (('d', "Direct upload"),
           ('tu', "Tumblr post"),
           ('tw', "Tweet"))

class User(Document):
    username = StringField(required=True, primary_key=True)
    password = StringField(required=True)
    auth = StringField(required=True, default=''.join(random.choice(string.hexdigits) for i in xrange(32)))

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        self.password = hashed
        self.save()

    def authenticate(self, password=None, auth=None):
        if auth and auth == self.auth:
            return True
        if not password:
            raise ValueError("Password or auth required")
        hashed = self.password
        return hashed and bcrypt.hashpw(password, hashed) == hashed

class Photo(Document):
    image_path = StringField(required=True)
    thumbnail_path = StringField(required=True)
    width = IntField(required=True)
    height = IntField(required=True)

    def as_dict(self):
        return {'image_path': self.image_path,
                'thumbnail_path': self.thumbnail_path,
                'width': self.width,
                'height': self.height}

class Post(Document):
    title = StringField(required=True)
    slug = StringField(required=True)
    date = DateTimeField(required=True, default=datetime.datetime.now)
    photos = ListField(ReferenceField(Photo), required=True)
    tags = ListField(StringField())
    source = StringField(required=True, choices=SOURCES)
    meta = {
        'indexes': [
            {'fields': ['slug'], 'unique': True, 'types': False}
        ]
    }

    def as_dict(self):
        date_str = self.date.strftime('%Y.%m.%d')
        photos_list = [p.as_dict() for p in self.photos]
        d = {'title': self.title,
                'slug': self.slug,
                'date': date_str,
                'source': self.source,
                'photos': photos_list}
        if hasattr(self, 'tags'):
            d['tags'] = self.tags
        return d
