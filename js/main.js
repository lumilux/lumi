(function() {
var Lumi = {
    index: 0,
    posts: [],
    postsBySlug: {},
    imageCache: {},
    CACHE_SIZE: 12,
    init: function(posts, path) {
        _.bindAll(this);

        if(path.indexOf('p/') === 0) {
            path = path.substr(2);
        }

        this.path = path;
        this.posts = posts;
        this.posts.reverse();

        _(this.posts).each(function(post, i) {
            post.index = i;
            this.postsBySlug[post.slug] = post;
        }, this);

        if(this.path) {
            this.index = this.postsBySlug[path].index;
            this.preload(this.posts, this.index + 1);
            this.preload(this.posts, this.index - 1);
            this.preload(this.posts, this.index + 2);
            this.preload(this.posts, this.index - 2);
        }
    },
    bindResize: function() {
        $(window).resize(this.onResize);
    },
    route: function(path) {
        history.pushState(null, '', '/' + path || '/');

        if(path.indexOf('p/') === 0) {
            path = path.substr(2);
        }

        this.path = path;
        $('body').removeClass();
        this.bindResize();
        this.render(path);
    },
    restoreScrollbar: function() {
        $('body').css('overflow', 'auto');
    },
    onResize: _.throttle(function() {
        window.clearTimeout(this.scrollbarHideTimeout);
        $('body').css('overflow', 'hidden');
        this.resize();
        this.scrollbarHideTimeout = window.setTimeout(this.restoreScrollbar, 100);
    }, 50),
    calcViewportDimensions: function() {
        var viewportHeight = $(window).height(),
            viewportWidth = $(window).width(),
            infoHeight = $('header').height() + $('footer').height() + 22;
        this.maxHeight = viewportHeight - infoHeight;
        this.viewportWidth = viewportWidth;
    },
    resize: function() {
        var self = this;
        this.calcViewportDimensions();

        var resizeImg = function() {
            var $this = $(this),
                width = this['data-width'] || parseInt($this.data('width'), 10),
                height = this['data-height'] || parseInt($this.data('height'), 10),
                maxWidth = self.maxHeight * (width / height);

            $this.css({
                'max-height': self.maxHeight + 'px',
                'max-width': maxWidth + 'px',
                'width': ''
            });

            if(width > height) {
                if(width > self.viewportWidth) {
                    $this.css({'width': '100%'});
                }
            }

            if(!$this.attr('src')) {
                $this.attr('src', $this.data('src'));
            }
        };

        $('#post img').each(resizeImg);
    },
    preload: function(posts, index) {
        if(index < 0 || index >= posts.length) { return; }
        var self = this,
            images = posts[index].photos

        if(_(images).size() + _(this.imageCache).size() > self.CACHE_SIZE) {
            this.imageCache = {};
        }

        _(images).each(function(image) {
            var path = image.image_path,
                width = image.width,
                height = image.height,
                img = $('<img />')[0];
            img.setAttribute('data-width', width);
            img.setAttribute('data-height', height);
            img['data-width'] = width;
            img['data-height'] = height;
            img.src = '/' + path;
            this.imageCache[path] = img;
            if(!this.maxHeight) { this.calcViewportDimensions(); }
            var maxWidth = this.maxHeight * (width / height);
            $(this.imageCache[path]).css({
                'max-width': maxWidth + 'px',
                'max-height': this.maxHeight + 'px'
            });
        }, this);
    },
    onAddChildren: function(query, func) {
        var MutationObserver = window.MutationObserver || window.WebKitMutationObserver || window.MozMutationObserver,
            list = document.querySelector(query),
            observer;

        if(!MutationObserver) { return; }

        observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if(mutation.addedNodes && mutation.addedNodes.length) {
                    var node = mutation.addedNodes[0];
                    if(node.complete) {
                        func();
                    } else {
                        $(node).load(func);
                    }
                }
            });
        });

        observer.observe(list, {
            attributes: true,
            childList: true,
            characterData: true
        });

        return observer;
    },
    insertTumblrButton: function() {
        var post = {
            'title': $('#title').text(),
            'slug': $('#share').data('slug'),
            'photos': [{'image_path': $('#post img')[0].src}],
            'tags': $('#share').data('tags')
        };
        $('#share').empty().append(this.tumblrButton(post));
    },
    tumblrButton: function(post) {
        var root = 'http://' + window.location.host + '/',
            image_path = post.photos[0].image_path,
            source = image_path.indexOf(root) === -1 ? root + image_path : image_path,
            clickThrough = root + 'p/' + post.slug,
            caption = '<a href="' + clickThrough + '">' + post.title + ' by Lumilux</a>',
            tags = post.tags && post.tags.length ? post.tags : 'photography',
            enc = window.encodeURIComponent,
            url = 'http://tumblr.com/share/photo?source=' + enc(source)
                  + '&caption=' + enc(caption)
                  + '&clickthru=' + enc(clickThrough)
                  + '&tags=' + enc(tags),
            onClick = "return !window.open(this.href, 'Share on Tumblr', 'width=400, height=400, centerscreen')";
        return '<a href="' + url + '" onclick="' + onClick + '" target="_blank" class="tumblr-button">Share on Tumblr</a>';
    },
    render: function(slug) {
        this.index = slug ? this.postsBySlug[slug].index : 0;
        var $post = $('#post'),
            post = this.posts[this.index],
            root = 'http://' + window.location.host + '/';
        document.title = post.title + " - Lumilux";
        window.scrollTo(0, 0);

        $('meta[name^="twitter"]').remove();
        $post.empty();

        if(!this.maxHeight) { this.calcViewportDimensions(); }

        _(post.photos).each(function(photo) {
            var img,
                dataWidth = ' data-width="' + photo.width + '"',
                dataHeight = ' data-height="' + photo.height + '"',
                style = ' style="width: auto; max-height: ' + this.maxHeight + 'px;"';
            if(_(this.imageCache).has(photo.image_path)) {
                img = this.imageCache[photo.image_path];
            } else {
                img = '<img src="/' + photo.image_path + '"' + dataWidth + dataHeight + style + ' />';
            }
            $post.append(img);
        }, this);
        this.resize();

        $('#title').text(post.title);
        $('#date').show().text(post.date);
        $('#share').attr('data-slug', null);
        $('#share').attr('data-tags', null);
        $('#share').empty().append(this.tumblrButton(post));

        if(this.index === this.posts.length - 1) {
            $('#prev').hide();
        } else {
            if(!$('#prev').length) { $('header ul').prepend('<li><a id="prev">&#x2190;</a></li>'); }
            $('#prev').show().attr('href', '/p/' + this.posts[this.index + 1].slug);
            this.preload(this.posts, this.index + 1);
            this.preload(this.posts, this.index + 2);
        }

        if(this.index === 0) {
            $('#next').hide();
        } else {
            if(!$('#next').length) { $('header ul').append('<li><a id="next">&#x2192;</a></li>'); }
            $('#next').show().attr('href', '/p/' + this.posts[this.index - 1].slug);
            this.preload(this.posts, this.index - 1);
            this.preload(this.posts, this.index - 2);
        }
    }
};
$(function() {
    var path = window.location.pathname.substring(1);

    if(path.search('archives') === 0) {
        $('#post dd').lazyload({
            'threshold': 100,
            'onAppear': function(loadOriginalImage) {
                var $noscript = $(this).find('noscript'),
                    noscript = $noscript[0],
                    noscriptText = noscript.innerText || noscript.textContent,
                    imagesText = noscriptText.replace(/src=/g, 'data-original='),
                    $images = $(imagesText);
                $images.each(function() {
                    var $this = $(this);
                    $this.attr('width', 100)
                         .attr('height', 100)
                         .attr('src', 'data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==')
                         .addClass('lazy-image');
                });
                $noscript.parent().append($images);
                $noscript.remove();
                $images.each(loadOriginalImage);
            }
        });
        return;
    }

    if(path && path.indexOf('p/') === -1) {
        return;
    }

    Lumi.resize();
    Lumi.insertTumblrButton();

    $.ajax({url: '/content/posts.json', dataType: 'json'})
    .done(function(data) {
        Lumi.init(data, path);
    });

    $(document).on('click', "a[href^='/p']", function(e) {
        if(!e.altKey && !e.ctrlKey && !e.metaKey && !e.shiftKey
           && (window.location.pathname === '/'
               || window.location.pathname.indexOf('/p/') === 0)) {
            e.preventDefault();
            Lumi.route($(e.currentTarget).attr("href").replace(/^\//, ""));
        }
    });

    $(document).on('keyup', function(e) {
        var isModifier = e.altKey || e.ctrlKey || e.metaKey || e.shiftKey
                         || _([16, 17, 18, 224]).contains(e.which);
        if(!isModifier && e.which === 37) {
            // left arrow key by itself
            if($('#prev').is(':visible')) { $('#prev').click(); }
        } else if(!isModifier && e.which === 39) {
            // right arrow key by itself
            if($('#next').is(':visible')) { $('#next').click(); }
        }
    });
});
}());

