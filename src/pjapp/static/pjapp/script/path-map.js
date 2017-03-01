$(function() {
    var $block = $('.path-structure'),
        $canvas = $block.find('.path-block-underlay'),
        $buttons = $('.path-link-buttons'),
        ctx = $canvas[0].getContext('2d'),
        COLOURS = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33','#a65628','#f781bf','#999999']; //http://colorbrewer2.org/
    
    var fromLinkCounts = {}, toLinkCounts = {};
    window.PATH_LINKS.forEach(function(link, i) {
        link.colour = COLOURS[i % COLOURS.length];
    });
    window.PATH_BLOCKS.push({'activity_id': '_START_', 'activity_name': 'Start of trajectory', 'pos_x': 0});
    window.PATH_BLOCKS.push({'activity_id': '_END_', 'activity_name': 'End of trajectory', 'pos_x': 1000});
    window.PATH_BLOCKS.forEach(function(b) {
        var linksFrom = _(window.PATH_LINKS).where({from: b.activity_id});
        linksFrom.forEach(function(l) {
            l.to_pos_x = (_(window.PATH_BLOCKS).findWhere({activity_id: l.to})||{}).pos_x || 0;
        });
        var ll = linksFrom.length;
        _(linksFrom).sortBy(function(l) { return l.to_pos_x; }).forEach(function(l, i) {
            l.fromXOffset = ( i - (ll-1) / 2 ) * 120 / (ll+1);
        });
        
        var linksTo = _(window.PATH_LINKS).where({to: b.activity_id});
        linksTo.forEach(function(l) {
            l.from_pos_x = (_(window.PATH_BLOCKS).findWhere({activity_id: l.from})||{}).pos_x || 0;
        });
        var ll = linksTo.length;
        _(linksTo).sortBy(function(l) { return l.from_pos_x; }).forEach(function(l, i) {
            l.toXOffset = ( i - (ll-1) / 2 ) * 120 / (ll+1);
        });
    });
    
    function redrawLinks() {
        var width = $block.width(),
            height = $block.height(),
            blockPos = $canvas.offset();
        $canvas.attr({
            width: width,
            height: height,
        });
        ctx.clearRect(0,0,width,height);
        window.PATH_LINKS.forEach(function(link) {
            var $fromBlock = $block.find(
                link.from === '_START_'
                ? 'div.start-block'
                : ('li.activity-block[data-activity-id="' + link.from + '"]')
            );
            var $toBlock = $block.find(
                link.to === '_END_'
                ? 'div.end-block'
                : ('li.activity-block[data-activity-id="' + link.to + '"]')
            );
            var fbPos = $fromBlock.offset(),
                tbPos = $toBlock.offset(),
                fromX = fbPos.left - blockPos.left + $fromBlock.width()/2 + link.fromXOffset,
                fromY = fbPos.top - blockPos.top + $fromBlock.height(),
                toX = tbPos.left - blockPos.left + $toBlock.width()/2 + link.toXOffset,
                toY = tbPos.top - blockPos.top;
            ctx.fillStyle = link.colour;
            ctx.strokeStyle = link.colour;
            ctx.beginPath();
            ctx.arc(fromX,fromY,5,0,2*Math.PI);
            ctx.fill();
            ctx.beginPath();
            ctx.moveTo(fromX, fromY);
            ctx.lineTo(fromX, fromY + 20);
            ctx.quadraticCurveTo(fromX, fromY + 40, (fromX+toX)/2, (fromY+toY+5)/2);
            ctx.quadraticCurveTo(toX, toY - 30, toX, toY - 10);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(toX, toY);
            ctx.lineTo(toX - 5, toY - 10);
            ctx.lineTo(toX + 5, toY - 10);
            ctx.fill();
            $buttons.find('li.link-button[data-link-id="' + link.id + '"]').css({
                left: fromX,
                top: fromY+5,
                background: link.colour,
            });
        });
    }
    var throttledRedrawLinks = _.throttle(redrawLinks, 200);
    $(window).on("resize scroll", function(e) {
        throttledRedrawLinks();
    });
    redrawLinks();
            
    var $removeLinkForm = $('#remove-link-form'),
        $addLinkForm = $('#add-link-form');
    
    $buttons.find('li.link-button').click(function() {
        var linkid = $(this).attr('data-link-id'),
            title = $(this).attr('title');
        if (confirm('Do you want to remove '+title)) {
            $removeLinkForm.find('input[name="link_id"]').val(linkid);
            $removeLinkForm.submit();
        }
    });
    var startBlock = null, startId = null;
    function resetBlocks() {
        startBlock.removeClass('active');
        startBlock = null;
        startId = null;           
    }
    $('body').click(function() {
        if (startBlock) {
            resetBlocks();
        }
    });
    $('a.join-path').click(function(e) {
        e.stopPropagation();
        var $this = $(this),
            $block = $this.parents('[data-activity-id]'),
            id = $block.attr('data-activity-id');
        if (!startBlock) {
            if (id === '_END_') {
                alert('A link cannot start from the end of trajectory!');
            } else {
                startBlock = $block;
                startId = id;
                startBlock.addClass('active');
            }
        } else {
            if (id !== startId) {
                if (id === '_START_') {
                    alert('A link cannot go towards the start of trajectory!');
                } else {
                    var _startid = parseInt(startId) || null;
                    var _endid =  parseInt(id) || null;
                    if (_startid !== _endid) {
                        console.log({'from':_startid,'to':_endid});
                        if (_(window.PATH_LINKS).findWhere({'from':_startid,'to':_endid})) {
                            alert('These two blocks are already linked!');
                        } else {
                            $addLinkForm.find('input[name="from_id"]').val(_startid);
                            $addLinkForm.find('input[name="to_id"]').val(_endid);
                            $addLinkForm.submit();
                        }
                    }
                }
            }
            resetBlocks();
        }
        return false;
    });
});
