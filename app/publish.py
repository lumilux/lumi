from itertools import tee, islice, chain, izip
import os
import re
import simplejson as json

from jinja2 import Environment, FileSystemLoader
from mongoengine import *

from tumblr import TumblrAPI
from models import User, Photo, Post
import image_utils

dn, rp, ap, relp, join = os.path.dirname, os.path.realpath, os.path.abspath, os.path.relpath, os.path.join
CWD = dn(__file__)
PARENT_DIR = rp(ap(join(CWD, '..')))
POSTS_PATH = rp(ap(join(CWD, '..', 'content/posts.json')))
INDEX_PATH = rp(ap(join(CWD, '..', 'index.html')))
ABOUT_PATH = rp(ap(join(CWD, '..', 'about.html')))
ARCHIVES_PATH = rp(ap(join(CWD, '..', 'archives.html')))
RSS_PATH = rp(ap(join(CWD, '..', 'rss.xml')))
TEMPLATES_DIR = rp(ap(join(CWD, 'templates')))
P_DIR = rp(ap(join(CWD, '../p/')))

SOURCES = {'DIRECT': 'd',
           'TUMBLR': 'tu',
           'TWITTER': 'tw'}

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def date_format(value, format='%Y.%m.%d'):
    return value.strftime(format)

env.filters['date_format'] = date_format

connect('lumi')

def prev_and_next(it):
    prevs, items, nexts = tee(it, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return izip(prevs, items, nexts)

def create_photo(file_path):
    photo_path, width, height = image_utils.fit_and_save(file_path)
    thumb_path = image_utils.generate_thumbnail(photo_path)
    photo_path, thumb_path = (relp(rp(p), PARENT_DIR) for p in (photo_path, thumb_path))
    photo = Photo(image_path=photo_path, thumbnail_path=thumb_path, width=width, height=height)
    photo.save()
    return photo

def create_post(title, slug=None, date=None, photos=None, tags=None, source=SOURCES['DIRECT']):
    if not slug:
        slug = title.lower()
        slug = re.sub(r'\s', '-', slug)
        slug = re.sub(r'[^a-zA-Z0-9-]', '', slug)
    post = Post(title=title, slug=slug, date=date, photos=photos, tags=tags, source=source)
    post.save()
    return post

def emit(post):
    with open(POSTS_PATH, 'r') as f:
        try:
            posts = json.load(f)
        except:
            posts = []
    with open(POSTS_PATH, 'w') as f:
        posts.append(post.as_dict())
        json.dump(posts, f)

def refresh():
    with open(POSTS_PATH, 'w') as f:
        posts = []
        for post in Post.objects.order_by('date'):
            posts.append(post.as_dict())
        json.dump(posts, f)

def generate_post_pages():
    posts = Post.objects.order_by('-date')
    for next, p, prev in prev_and_next(posts):
        title, slug, date, photos = p.title, p.slug, p.date, p.photos
        prev_path = '/p/' + prev.slug if prev else None
        next_path = '/p/' + next.slug if next else None
        try:
            tags = p.tags
        except AttributeError:
            tags = None

        page_template = env.get_template('index.html')
        page = page_template.render(title=title, slug=slug, date=date, photos=photos, tags=tags, prev_path=prev_path, next_path=next_path).encode('utf-8')
        with open(rp(ap(join(P_DIR, slug + '.html'))), 'w') as f:
            f.write(page)

def generate():
    posts = Post.objects.order_by('-date')[:2]
    title, slug, date, photos = posts[0].title, posts[0].slug, posts[0].date, posts[0].photos
    prev_path = '/p/' + posts[1].slug
    try:
        tags = posts[0].tags
    except AttributeError:
        tags = None

    index_template = env.get_template('index.html')
    index_page = index_template.render(title=title, slug=slug, date=date, photos=photos, tags=tags, prev_path=prev_path).encode('utf-8')
    with open(INDEX_PATH, 'w') as f:
        f.write(index_page)

    about_template = env.get_template('about.html')
    about_page = about_template.render().encode('utf-8')
    with open(ABOUT_PATH, 'w') as f:
        f.write(about_page)

    all_posts = Post.objects.order_by('-date')
    archives_template = env.get_template('archives.html')
    archives_page = archives_template.render(posts=all_posts).encode('utf-8')
    with open(ARCHIVES_PATH, 'w') as f:
        f.write(archives_page)

    generate_post_pages()
    generate_rss()

def generate_rss():
    all_posts = Post.objects.order_by('-date')
    rss_template = env.get_template('rss.xml')
    rss_file = rss_template.render(posts=all_posts).encode('utf-8')
    with open(RSS_PATH, 'w') as f:
        f.write(rss_file)

def delete_last():
    post = Post.objects.order_by('-date')[0]
    d = post.as_dict()
    photos = post.photos
    post.delete()
    for p in photos:
        p.delete()
    return d

def publish_tumblr(post, tumblr):
    caption = '<a href="http://lumilux.org/p/{0}"><em>{1}</em> by Lumilux</a>'.format(post.slug, post.title)
    post_url = 'http://lumilux.org/p/{0}'.format(post.slug)

    params = {
        'type': 'photo',
        'caption': caption,
        'link': post_url,
        'slug': post.slug,
    }

    for i, photo in enumerate(post.photos):
        abs_path = rp(ap(join(PARENT_DIR, photo.image_path)))
        params['data[{0}]'.format(i)] = file(abs_path, 'rb').read()

    if hasattr(post, 'tags') and post.tags:
        params['tags'] = ','.join(post.tags)
    else:
        params['tags'] = 'photography'

    tumblr = TumblrAPI(tumblr)
    post = tumblr.post('lumilux.tumblr.com', params);
