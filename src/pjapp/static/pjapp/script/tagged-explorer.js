$(function() {
    $('.tagged-explorer').each(function() {
        var $te = $(this),
            $tags = $te.find('li.filter-tag'),
            $search = $te.find('input.explorer-search'),
            $items = $te.find('li.item'),
            currentTag = null;
        $search.keyup(function() {
            $tags.removeClass('active');
            currentTag = null;
            $items.find('.highlight').removeClass('highlight');
            var val = $search.val();
            if (val.length > 2) {
                var lowerval = val.toLowerCase();
                $items.each(function() {
                    var $item = $(this),
                        itemSearch = $item.attr('data-search-index') || $item.text().toLowerCase();
                    if (itemSearch.indexOf(lowerval) !== -1) {
                        $item.find('li.item-tag,p.item-description,.title-name').each(function() {
                            var $highlightable = $(this),
                                content = $highlightable.text(),
                                lowercontent = content.toLowerCase(),
                                startPos = lowercontent.indexOf(lowerval);
                            if (startPos !== -1) {
                                var $p = $('<p>');
                                $('<span>').text(content.substr(0, startPos)).appendTo($p);
                                $('<span class="highlight">').text(content.substr(startPos, val.length)).appendTo($p);
                                $('<span>').text(content.substr(startPos + val.length)).appendTo($p);
                                $highlightable.html($p.html());
                            }
                        });
                        $item.show();
                    } else {
                        $item.hide();
                    }
                });
            } else {
                $items.show();
            }
        });
        $te.find('.empty-explorer-search').click(function() {
            if ($search.val()) {
                $search.val('');
                $items.show();
                $items.find('.highlight').removeClass('highlight');
            }
            return false;
        });
        $tags.click(function() {
            var $tag = $(this),
                tagVal = $tag.attr('data-tag-id');
            $tags.removeClass('active');
            $search.val('');
            $items.find('.highlight').removeClass('highlight');
            if (tagVal === currentTag) {
                currentTag = null;
                $items.show();
            } else {
                currentTag = tagVal;
                $tag.addClass('active');
                $items.each(function() {
                    var $item = $(this),
                        $tags = $item.find('li.item-tag[data-tag-id="' + tagVal + '"]');
                    if ($tags.length) {
                        $tags.addClass('highlight');
                        $item.show();
                    } else {
                        $item.hide();
                    }
                });
            }
        });
    });
});
