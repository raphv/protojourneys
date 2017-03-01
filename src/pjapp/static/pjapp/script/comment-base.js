$(function() {
    var $commentform = $('#comment-form'),
        $imgbutton = $commentform.find('div.image-button'),
        $fileinput = $imgbutton.find('input[type=file]'),
        $filepreview = $imgbutton.find('img'),
        $fileremove = $imgbutton.find('div.remove');
    
    $filepreview.on('load', function() {
        var w1 = $imgbutton.width(),
            h1 = $imgbutton.height(),
            w2 = this.width,
            h2 = this.height,
            ratio = Math.min(1, Math.max(w1/w2, h1/h2)),
            wr = w2 * ratio,
            hr = h2 * ratio;
        $filepreview.css({
            width: wr,
            height: hr,
            left: (w1 - wr)/2,
            top: (h1 - hr)/2,
            display: 'block'
        });
        $fileremove.show();
    });
    
    $fileinput.on('change', function() {
        if (this.files.length) {
            var reader = new FileReader();
            reader.onload = function() {
                $filepreview.attr('src', reader.result);
            };
            reader.readAsDataURL(this.files[0]);
        }
    });
    
    $fileremove.click(function(e) {
        resetImage();
        e.stopPropagation();
    });
    
    $imgbutton.click(function(e) {
        if (e.target != $fileinput[0]) {
            $fileinput.click();
        }
    });
        
    function resetForm() {
        $commentform.removeClass('pending');
        $commentform.find('#invert-comment-public i').removeClass('fa-check-square-o').addClass('fa-square-o');
        $commentform.find('#comment-public-field').val('0');
        $commentform.find('textarea').val('');
        $fileinput.val('');
        $filepreview.hide();
        $fileremove.hide();
    }
        
    $commentform.on('submit', function(e) {
        e.preventDefault();
        if (!$commentform.hasClass('pending')) {
            $commentform.addClass('pending');
            var formData = new FormData();
            $commentform.find('input[type=hidden]').each(function() {
                formData.append(this.name, this.value);
            });
            formData.append('content', $commentform.find('textarea').val());
            var files = $fileinput[0].files;
            if (files.length) {
                formData.append('image', files[0]);
            }
            var req = new XMLHttpRequest();
            req.onload = function(e) {
                if (req.status == 200) {
                    $('.comment-list').prepend(req.responseText);
                    $('.comment-count').text($('.comment-list li').length);
                    $commentform.find('.comment-outcome.onsuccess').show();
                } else {
                    $commentform.find('.comment-outcome.onerror').show();
                }
                resetForm();
            };
            req.open('POST', window.AJAX_COMMENT_ENDPOINT, true);
            req.send(formData);
        }
    });
    
    $('.comment-outcome').click(function() {
        $(this).hide();
    });
    
    $('.rating-widget').each(function() {
        var $this = $(this);
        
        function clickStar(star) {
            var $star = $(this),
                val = $star.attr('data-rating');
            $('#comment-rating-field').val(val);
            $this.find('i').each(function() {
                var $other = $(this);
                if (parseInt($other.attr('data-rating')) > parseInt(val)) {
                    $other.removeClass('fa-star').addClass('fa-star-o');
                } else {
                    $other.addClass('fa-star').removeClass('fa-star-o');
                }
            });
        }
        
        for (var i = 1; i <6; i++) {
            var $star = $('<i class="fa fa-star-o"></i>');
            $star.attr('data-rating',i);
            $star.click(clickStar);
            $star.appendTo(this);
            $(this).append('<span> </span>');
        }
    });
    $('#invert-comment-public').click(function() {
        var $btn = $(this),
            $commfield = $('#comment-public-field'),
            $i = $btn.find('i');
        $i.removeClass('fa-square-o fa-check-square-o');
        $commfield.val(+!+$commfield.val());
        if (+$commfield.val()) {
            $i.addClass('fa-check-square-o');
        } else {
            $i.addClass('fa-square-o');
        }
    });
});
