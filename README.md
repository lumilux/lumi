lumi
====
### backend dependencies
* nginx
* web.py
* mongoengine
* pymongo
* mongodb
* PIL
* tumblpy

### frontend dependencies (included)
* underscore
* jquery
* dropzone

### each post:
* contains one or more photos
* has a title
* will be posted to tumblr

### publishing workflow
1. select photo(s) and write a title
2. hit "publish"  
   ↪ files are uploaded/saved, thumbnails are generated, and `PhotoObj`s are created  
   ↪ a `PostObj` is created with the title and the `PhotoObj` ids  
   ↪ the `PostObj` is appended to a json file with expanded `PhotoObj`s  
   ↪ `index.html` is generated with the latest post

### todo
* tweet each post
* editing and deleting posts in admin
* post from tumblr
* large nav click targets for mobile
