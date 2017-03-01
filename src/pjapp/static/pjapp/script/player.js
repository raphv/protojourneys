$(function() {
    $('button.base-destination').click(function() {
        $('#custom-activity-field').val('');
        $('#next-activity-field').val($(this).attr('data-activity-id'));
        $('#canonical-field').val($(this).attr('data-is-canonical'));
    });
    $('button.custom-destination').click(function() {
        $('#custom-activity-field').val($(this).attr('data-custom-activity-id'));
        $('#next-activity-field').val('');
        $('#canonical-field').val('');
    });
    $('button.create-custom-destination').click(function() {
        $('#custom-activity-field').val('CREATE');
        $('#next-activity-field').val('');
        $('#canonical-field').val('');
    });
    
    var $f = $(".action-bar");
    
    if ($f.length) {
        $(".main-section").css("margin-bottom",$f.height());
    }
    
    $('div.lightbox-background,a.lightbox-closer,p.comment-outcome').click(function() {
        $('#comment-lightbox,#map-lightbox,div.lightbox-container,#comment-lightbox .comment-outcome').hide();
    });
    
    $('#action-done').click(function() {
        $('#step-status-field').val('D');
        $('#finish-step-form').submit();
        return false;
    });
    $('#action-skip').click(function() {
        $('#step-status-field').val('S');
        $('#finish-step-form').submit();
        return false;
    });
    $('#action-comment,#switch-to-comment').click(function() {
        $('#map-lightbox').hide();
        $('#comment-lightbox,div.lightbox-container').show();
        return false;
    });
    $('#action-map').click(function() {
        $('#comment-lightbox').hide();
        $('#map-lightbox,div.lightbox-container').show();
        return false;
    });
    
    $('.show-non-canonical').click(function() {
        $('#non-canonical').toggle();
        return false;
    });
    
});