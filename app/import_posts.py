import datetime
import os
import simplejson as json
import time

from mongoengine import *
import requests

from models import Photo, Post
from publish import *
import image_utils

connect('lumi')

TXP_POSTS_PATH = rp(ap(join(CWD, 'txp_posts.json')))
TXP_IMAGES_PATH = rp(ap(join(CWD, 'txp_images.json')))
PHOTOS_DIR = rp(ap(join(CWD, '../img/photo')))
THUMBS_DIR = rp(ap(join(CWD, '../img/thumb')))
REMOTE_IMAGES_PATH = 'http://lumilux.org/images/'

posts = []
photos = {}
posts_data = []
photos_data = []

with open(TXP_POSTS_PATH, 'r') as po:
    posts_data = json.load(po)

with open(TXP_IMAGES_PATH, 'r') as ph:
    photos_data = json.load(ph)

for p in posts_data:
    if p['ID'] < 0:
        continue
    title = p['Title']
    date = time.strftime('%Y.%m.%d', time.strptime(p['feed_time'], '%Y-%m-%d'))
    slug = p['url_title']
    photo_ids = str(p['Image']).split(',')
    post = {'title': title,
            'date': date,
            'slug': slug,
            'photo_ids': photo_ids}
    posts.append(post)

for p in photos_data:
    id = str(p['id'])
    orig_filename = p['name']
    filename = id + '.jpg'
    image_file = REMOTE_IMAGES_PATH + id + '.jpg'
    thumb_file = REMOTE_IMAGES_PATH + id + 't.jpg'
    photo = {'image_file': image_file,
             'thumb_file': thumb_file,
             'orig_filename': orig_filename,
             'filename': filename}
    photos[id] = photo

with open(rp(ap(join(CWD, 'txp_posts_parsed.json'))), 'w') as po:
    json.dump(posts, po)

with open(rp(ap(join(CWD, 'txp_images_parsed.json'))), 'w') as ph:
    json.dump(photos, ph)

print posts[0]
print posts[-1]
print photos['1']
print photos['591']

def download_all():
    for i, po in enumerate(posts):
        print 'Downloading images for post', i
        for ph in po['photo_ids']:
            image = requests.get(photos[ph]['image_file'])
            thumb = requests.get(photos[ph]['thumb_file'])

            with open(rp(ap(join(PHOTOS_DIR, photos[ph]['filename']))), 'wb') as ph_f:
                ph_f.write(image.content)

            with open(rp(ap(join(THUMBS_DIR, photos[ph]['filename']))), 'wb') as th_f:
                th_f.write(thumb.content)

            print "Downloaded", ph
            time.sleep(0.25)

#download_all()

for i, po in enumerate(posts):
    po_photos = []
    for ph in po['photo_ids']:
        ph = photos[ph]
        image_path = 'img/photo/' + ph['filename']
        thumb_path = 'img/thumb/' + ph['filename']
        photo = Photo(image_path=image_path, thumbnail_path=thumb_path)
        photo.save()
        po_photos.append(photo)
    date = datetime.datetime.strptime(po['date'], '%Y.%m.%d')
    title = po['title']
    if not isinstance(title, basestring):
        title = unicode(title)
    title = title.encode('utf-8')
    slug = po['slug'].encode('utf-8')
    post = create_post(title=title, slug=slug, photos=po_photos, date=date)
    print "Saved post", i, "with photos", po['photo_ids']
