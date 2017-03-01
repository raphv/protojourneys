$(function() {
    var $h = $("header"),
        $w = $(window),
        $m = $(".main-section");
    
    var isBelow = false;
    
    function positionTopBar() {
        var scrollTop = $w.scrollTop(),
            limit = (isBelow ? 20 : 50);
        if (scrollTop > limit) {
            $h.addClass('collapsed');
            isBelow = true;
        } else {
            $h.removeClass('collapsed');
            isBelow = false;
        }
        $m.css("margin-top",$h.outerHeight());
    }
    var throttledPositionTopBar = _.throttle(positionTopBar, 50);
    $(window).on("resize scroll", function(e) {
        throttledPositionTopBar();
    });
    positionTopBar();
    
    $('.copiable-input').click(function() {
        this.focus();
        this.setSelectionRange(0, this.value.length);
        document.execCommand('copy');
    });
});
