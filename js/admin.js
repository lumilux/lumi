(function() {
'use strict';
var Login = {
    init: function() {
        _.bindAll(this);
        this.$el = $('#login');
        this.$el.on('submit', this.submit);
    },
    submit: function(e) {
        e.preventDefault();
        var data = {
            username: $('#username').val().trim(),
            password: $('#password').val().trim()
        };
        $.post('/admin/login', data).done(this.success).fail(this.error);
    },
    success: function(response) {
        if(!response.success) { this.error(); }
        window.location.href = '/admin/';
    },
    error: function() {
        this.$el.find('input').val('');
        $('#error').text("Could not log in.");
    }
};

var Admin = {
    fileIds: [],
    numFilesUploaded: 0,
    init: function() {
        _.bindAll(this);
        var self = this;
        this.photoDropzone = new Dropzone('#photo-dropzone', {
            url: '/admin/upload',
            maxFilesize: 50,
            paramName: 'file',
            enqueueForUpload: false,
            accept: function(file, done) {
                console.log("pushing " + file.name + " onto queue");
                this.filesQueue.push(file);
                self.numFilesPushed = this.filesQueue.length;
                done();
            }
        });
        $('#publish-post').on('submit', this.submitPublish);
    },
    submitPublish: function(e) {
        e.preventDefault();
        $('#publish-post').addClass('disabled');
        $('#photo-dropzone').addClass('no-events');
        this.photoDropzone.processQueue();
        this.photoDropzone.on('success', this.uploadSuccess);
        this.photoDropzone.on('error', this.uploadError);
    },
    uploadSuccess: function(file, response) {
        this.numFilesUploaded += 1;
        this.fileIds.push(response.id);
        if(this.numFilesPushed === this.numFilesUploaded) {
            this.uploadingDone(this.fileIds);
        }
    },
    uploadError: function(file, errorMsg) {
        this.photoDropzone.removeFile(file);
    },
    uploadingDone: function(fileIds) {
        console.log('all done');
        console.log(fileIds);
        var title = $('#title').val().trim();
        var tags = $('#tags').val().trim();
        var data = {title: title, photos: fileIds};
        if(tags) { data.tags = tags; }
        $.post('/admin/publish', JSON.stringify(data)).done(this.success).fail(this.error);
    },
    success: function(response) {
        if(!response.success) { this.error(); }
        $('#publish-post').remove();
        this.photoDropzone.disable();
        this.photoDropzone.enable();
        this.init();
        var title = response.post.title;
        var url = '/p/' + response.post.slug;
        $('body').append('<p class="success"><a href="' + url + '">' + title + '</a></p>');
        window.location.href = url;
    },
    error: function() {
        $('#publish-post').removeClass('disabled');
        $('#error').text("Could not publish post.");
    }
};
$(function() {
    var path = window.location.pathname.split('/admin')[1];
    var routes = {
        '/login': Login,
        '/': Admin
    };
    if(_(routes).has(path)) {
        routes[path].init();
    }
});
})();
