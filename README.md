lumi
====
### backend dependencies
* nginx
* cherrypy
* mongoengine
* pymongo
* mongodb
* PIL

### frontend dependencies (included)
* underscore
* jquery
* dropzone

### publishing use cases
1. upload one or more photos directly
2. tweet one photo #lumilux
3. post one photo to tumblr #lumilux

### each post:
* contains one or more photos
* has a title
* will be tweeted
* will be posted to tumblr

### publishing workflow
1. select photo(s) and write a title  
   _or_  
   tweet or post a photo on tumblr
2. hit "publish"  
   ↪ files are uploaded/saved, thumbnails are generated, and `PhotoObj`s are created  
   ↪ a `PostObj` is created with the title and the `PhotoObj` ids  
   ↪ the `PostObj` is appended to a json file with expanded `PhotoObj`s  
   ↪ `index.html` is generated with the latest post

### todo
* generate atom/rss feed
* editing and deleting posts in admin
* generate static pages for all posts
* post from tumblr
* large nav click targets for mobile
